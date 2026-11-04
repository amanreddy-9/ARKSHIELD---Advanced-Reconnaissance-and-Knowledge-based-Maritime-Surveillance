"""
tracking/track.py
Persistent Maritime Vessel Track Class.

Encapsulates:
- Track identity and lifecycle states (tentative, confirmed, lost, deleted)
- Internal 8D Kalman filter for continuous motion & scale prediction
- Occlusion persistence and coasting history
- Diagnostic attributes for pipeline & telemetry integration
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from tracking.kalman_filter import KalmanFilter
from tracking.association import measurement_for_track


class Track:
    """
    Represents an individual maritime vessel track under aerial surveillance.
    Integrates an 8-state linear Kalman filter for position, dimension,
    and velocity estimation across frames.
    """

    STATE_TENTATIVE = "tentative"
    STATE_CONFIRMED = "confirmed"
    STATE_LOST = "lost"
    STATE_DELETED = "deleted"

    def __init__(self, track_id: int, detection: Dict[str, Any], timestamp=0.0, time_aware=False, confirm_hits=2):
        """
        Instantiate a new vessel track from an initial detection.

        Args:
            track_id: Unique integer identifier.
            detection: Detection dictionary containing either:
                       - 'bbox': [x1, y1, x2, y2]
                       - or 'cx', 'cy', 'w', 'h'
                       and 'confidence' / 'conf'.
        """
        self.track_id = int(track_id)
        self.id = self.track_id  # Backwards compatibility alias

        # Extract initial geometry
        bbox = detection.get("bbox")
        if bbox is not None and len(bbox) == 4:
            x1, y1, x2, y2 = [float(v) for v in bbox]
            w = max(1.0, x2 - x1)
            h = max(1.0, y2 - y1)
            cx = x1 + w / 2.0
            cy = y1 + h / 2.0
        else:
            cx = float(detection.get("cx", 0.0))
            cy = float(detection.get("cy", 0.0))
            w = max(1.0, float(detection.get("w", 10.0)))
            h = max(1.0, float(detection.get("h", 10.0)))

        self.confidence = float(detection.get("confidence", detection.get("conf", 1.0)))

        # Instantiate Kalman Filter
        self.kf = KalmanFilter()
        self.kf.initialize(np.array([cx, cy, w, h]), velocity_scale=30.0 if time_aware else 1.0)
        self.time_aware = time_aware
        self.confirm_hits = confirm_hits
        self.created_at = self.last_measurement_at = self.timestamp = float(timestamp)
        self.seconds_since_measurement = 0.0
        self.age_seconds = 0.0
        self.inference_opportunities = 1
        self.detector_misses = 0
        self.total_detector_misses = 0
        self.observed = True
        self.recovered = False
        self.last_center = np.array([cx, cy])
        self.predicted_bbox = None
        self.matching_stage = None
        self.matching_cost = None
        self.dt = 1.0
        self.reference_size = np.array([w,h],dtype=float)
        self.measurement_components = [0,1,2,3]
        self.camera_velocity = np.zeros(4)
        self.pre_prediction_geometry = self.kf.state[:4].copy()

        # Track lifecycle metadata
        self.age = 1
        self.hits = 1
        self.hit_streak = 1
        self.confirmed_at = self.timestamp if confirm_hits <= 1 else None
        self.missed_frames = 0
        self.tracking_state = self.STATE_CONFIRMED if confirm_hits <= 1 else self.STATE_TENTATIVE

    # -------------------------------------------------------------
    # Properties for Seamless Compatibility
    # -------------------------------------------------------------

    @property
    def missed(self) -> int:
        """Alias for missed_frames."""
        return self.missed_frames

    @missed.setter
    def missed(self, val: int):
        self.missed_frames = int(val)

    @property
    def state(self) -> str:
        """Alias for tracking_state."""
        return self.tracking_state

    @state.setter
    def state(self, val: str):
        self.tracking_state = str(val)

    @property
    def cx(self) -> float:
        return self.kf.centroid[0]

    @property
    def cy(self) -> float:
        return self.kf.centroid[1]

    @property
    def w(self) -> float:
        return self.kf.size[0]

    @property
    def h(self) -> float:
        return self.kf.size[1]

    @property
    def vx(self) -> float:
        return self.kf.velocity[0]

    @property
    def vy(self) -> float:
        return self.kf.velocity[1]

    @property
    def centroid(self) -> Tuple[float, float]:
        """Return (cx, cy) tuple."""
        return (self.cx, self.cy)

    @property
    def bounding_box(self) -> List[float]:
        """Return [x1, y1, x2, y2] bounding box."""
        hw = self.w / 2.0
        hh = self.h / 2.0
        return [self.cx - hw, self.cy - hh, self.cx + hw, self.cy + hh]

    @property
    def bbox(self) -> List[float]:
        """Alias for bounding_box."""
        return self.bounding_box

    # -------------------------------------------------------------
    # Motion Prediction and Measurement Update
    # -------------------------------------------------------------

    def predict(self, dt=1.0, timestamp=None, inference_ran=True):
        self.dt = dt
        self.pre_prediction_geometry = self.kf.state[:4].copy()
        pred = self.kf.predict(dt)
        self.timestamp = self.timestamp+dt if timestamp is None else timestamp
        self.age += 1
        self.age_seconds = self.timestamp-self.created_at
        self.missed_frames += 1
        self.seconds_since_measurement = self.timestamp-self.last_measurement_at
        self.observed = self.recovered = False
        self.matching_cost = self.matching_stage = None
        if inference_ran:
            self.inference_opportunities += 1
            self.detector_misses += 1
            self.total_detector_misses += 1
        if self.tracking_state != self.STATE_TENTATIVE:
            self.tracking_state = self.STATE_LOST
        self.predicted_bbox = self.bbox.copy()
        return pred

    def compensate_camera(self, affine):
        """Apply camera control while keeping velocity in apparent image px/second.
        Prediction already includes the previous camera component. Subtract that
        expected displacement before adding the new affine displacement, once.
        Thus unreliable/occluded camera estimates fall back to ordinary prediction.
        """
        a=np.asarray(affine,dtype=float)[:,:2];offset=np.asarray(affine)[:,2]
        geometry=np.zeros((4,4));geometry[:2,:2]=a;geometry[2:,2:]=np.abs(a)
        j=np.zeros((8,8));j[:4,:4]=geometry;j[4:,4:]=geometry
        old_camera=geometry@self.camera_velocity
        shift=np.array([offset[0],offset[1],0.,0.])
        new_camera=(geometry@self.pre_prediction_geometry+shift-self.pre_prediction_geometry)/self.dt if self.dt>0 else np.zeros(4)
        self.kf.x=j@self.kf.x
        self.kf.x[:4,0]+=shift-old_camera*self.dt
        self.kf.x[4:,0]+=new_camera-old_camera
        self.camera_velocity=new_camera
        self.reference_size=geometry[2:,2:]@self.reference_size
        self.kf.P=j@self.kf.P@j.T;self.kf.P=(self.kf.P+self.kf.P.T)*.5
        self.last_center=a@self.last_center+offset
        self.kf._valid_size();self.predicted_bbox=self.bbox.copy()

    def update(self, detection: Dict[str, Any]) -> None:
        """
        Incorporate a new matched detection into the Kalman filter.
        Resets missed frame counter and increments hits.
        """
        bbox = detection.get("bbox")
        if bbox is not None and len(bbox) == 4:
            x1, y1, x2, y2 = [float(v) for v in bbox]
            w = max(1.0, x2 - x1)
            h = max(1.0, y2 - y1)
            cx = x1 + w / 2.0
            cy = y1 + h / 2.0
        else:
            cx = float(detection.get("cx", self.cx))
            cy = float(detection.get("cy", self.cy))
            w = max(1.0, float(detection.get("w", self.w)))
            h = max(1.0, float(detection.get("h", self.h)))

        # Update Kalman Filter
        z = np.array([cx, cy, w, h])
        was_coasting = self.confirmed_at is not None and self.seconds_since_measurement > (0.25 if self.time_aware else 3.0)
        z,mask=measurement_for_track(detection,self)
        self.kf.update(z, detection.get("confidence", detection.get("conf", 1.0)),mask)
        self.measurement_components=np.flatnonzero(mask).tolist()
        if mask.all(): self.reference_size=.9*self.reference_size+.1*z[2:]
        self.last_center = self.kf.state[:2].copy()
        self.last_measurement_at = self.timestamp
        self.seconds_since_measurement = 0.0
        self.observed = True
        self.recovered = was_coasting
        if self.detector_misses > 0:
            self.total_detector_misses -= 1
        self.detector_misses = 0

        # Update confidence
        self.confidence = float(detection.get("confidence", detection.get("conf", self.confidence)))

        # Reset counters
        self.missed_frames = 0
        self.hits += 1
        self.hit_streak += 1

        # Confirm after the configured number of valid associations (skips are not misses).
        if self.tracking_state == self.STATE_TENTATIVE and self.hit_streak >= self.confirm_hits:
            self.tracking_state = self.STATE_CONFIRMED
            self.confirmed_at = self.timestamp
        elif self.tracking_state == self.STATE_LOST:
            self.tracking_state = self.STATE_CONFIRMED

    def mark_missed(self) -> None:
        """Explicitly record a missed detection without double-predicting."""
        self.missed_frames += 1
        self.hit_streak = 0
        if self.tracking_state == self.STATE_CONFIRMED:
            self.tracking_state = self.STATE_LOST

    def to_dict(
        self,
        detection_index: Optional[int] = None,
        matched_detection: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Export track representation dictionary for pipeline and API serialization.
        """
        hw = self.w / 2.0
        hh = self.h / 2.0
        return {
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "last_measurement_at": self.last_measurement_at,
            "confirmed_identity": self.confirmed_at is not None,
            "prediction_reason": None if self.observed else ("detector_miss" if self.detector_misses else "inference_skipped"),
            "track_id": self.track_id,
            "cx": round(self.cx, 2),
            "cy": round(self.cy, 2),
            "w": round(self.w, 2),
            "h": round(self.h, 2),
            "bbox": [
                round(self.cx - hw, 2),
                round(self.cy - hh, 2),
                round(self.cx + hw, 2),
                round(self.cy + hh, 2),
            ],
            "bounding_box": [
                round(self.cx - hw, 2),
                round(self.cy - hh, 2),
                round(self.cx + hw, 2),
                round(self.cy + hh, 2),
            ],
            "centroid": (round(self.cx, 2), round(self.cy, 2)),
            "kalman_state": self.kf.state.tolist(),
            "covariance_diagonal": np.diag(self.kf.P).tolist(),
            "vx": round(self.vx, 2),
            "vy": round(self.vy, 2),
            "observed": self.observed,
            "recovered": self.recovered,
            "status": "RECOVERED" if self.recovered else ("DETECTED" if self.observed else "PREDICTED"),
            "lifecycle_state": "recovered" if self.recovered else ("coasting" if not self.observed and self.confirmed_at is not None else self.tracking_state),
            "seconds_since_measurement": self.seconds_since_measurement,
            "age_seconds": self.age_seconds,
            "inference_opportunities": self.inference_opportunities,
            "detector_misses": self.detector_misses,
            "total_detector_misses": self.total_detector_misses,
            "velocity_units": "pixels/second" if self.time_aware else "pixels/update",
            "predicted_bbox": self.predicted_bbox or self.bbox,
            "measurement_components": self.measurement_components if self.observed else [],
            "matching_stage": self.matching_stage,
            "matching_cost": self.matching_cost,
            "confidence": round(self.confidence, 4),
            "missed": self.missed_frames,
            "missed_frames": self.missed_frames,
            "age": self.age,
            "hits": self.hits,
            "state": self.tracking_state,
            "tracking_state": self.tracking_state,
            "detection_index": detection_index,
            "matched_detection": matched_detection,
        }
