import os
# pipeline/orchestrator.py

from collections import defaultdict, Counter
from datetime import datetime
import json
from pathlib import Path
import shutil
import tempfile
import cv2
from uuid import uuid4
from tracking.camera_motion import CameraMotionEstimator
from tracking.telemetry import TrackingDiagnosticCSV, draw_tracking
from pipeline.track_registry import build_track_registry

from models.detector import VesselDetector
from models.classifier import ShipClassifier
from models.groq_vlm import GroqVLM
from rl.scheduler import AdaptiveComputeScheduler
from tracking.tracker import VesselTracker


class OATrackPipeline:
    """
    Main OATrack-VLM processing pipeline.

    Satellite mode:
        Image -> YOLO vessel detection -> VLM analysis

    Drone mode:
        MP4/frame -> YOLO vessel detection -> tracking ->
        ConvNeXt classification -> temporal classification aggregation

    RL:
        Selects lightweight / standard / heavy processing mode
        based on target visibility and scene complexity.
    """

    def __init__(self):
        # ---------------------------------------------------------
        # Models
        # ---------------------------------------------------------
        self.detector = VesselDetector()
        self.classifier = ShipClassifier()
        self.vlm = GroqVLM()

        # ---------------------------------------------------------
        # RL / adaptive compute scheduler
        # ---------------------------------------------------------
        self.scheduler = AdaptiveComputeScheduler()

        # ---------------------------------------------------------
        # Tracker
        # ---------------------------------------------------------
        self.tracker = VesselTracker(confirm_hits=3)  # birth + two consecutive successful associations

        # ---------------------------------------------------------
        # Temporal classification history
        #
        # Each Track ID maintains:
        #   - confidence-weighted class scores
        #   - number of observations for each class
        #   - last frame seen
        # ---------------------------------------------------------
        self.track_class_scores = defaultdict(
            lambda: defaultdict(float)
        )

        self.track_class_counts = defaultdict(Counter)

        self.track_last_seen = {}

        # Cache for Vision-Language multimodal disambiguation per Track ID
        self.track_vlm_cache = {}

    # ============================================================
    # TEMPORAL CLASSIFICATION
    # ============================================================

    def _update_track_classification(
        self,
        track_id,
        classification,
        frame_index=None,
    ):
        """
        Convert noisy frame-level classifications into a
        temporally stable Track ID classification.

        Example:

            Frame 20 -> Oil tanker 0.91
            Frame 21 -> Oil tanker 0.96
            Frame 22 -> Frigate 0.55
            Frame 23 -> Oil tanker 0.98

        Stable result:
            Oil tanker

        'stability' represents the accumulated evidence share,
        NOT a calibrated classifier probability.
        """

        if not classification:
            return None

        label = classification.get("label")

        if not label:
            return None

        try:
            confidence = float(
                classification.get("confidence", 0.0)
            )
        except (TypeError, ValueError):
            confidence = 0.0

        track_id = int(track_id)

        # --------------------------------------------------------
        # Confidence-weighted evidence; external VLM predictions are not ground truth
        # --------------------------------------------------------
        if classification.get("vlm_reasoned"):
            weight = max(min(confidence, 1.0), 0.01)  # VLM output is evidence, never ground truth
        else:
            weight = max(confidence, 0.01)

        probabilities = classification.get("probabilities")
        if probabilities and not classification.get("vlm_reasoned"):
            # Preserve runner-up evidence instead of turning a close call into
            # a full vote for the winner on every frame.
            import math
            values = {candidate:float(probability) for candidate,probability in probabilities.items()}
            if not all(math.isfinite(v) and v >= 0 for v in values.values()) or sum(values.values()) <= 0:
                raise ValueError("Invalid class probability vector")
            total = sum(values.values())
            evidence_weight = max(0., min(1., float(classification.get("detector_confidence", 1.)))) * max(0., min(1., float(classification.get("crop_quality_weight",1.))))
            for candidate, probability in values.items():
                self.track_class_scores[track_id][candidate] += evidence_weight*probability/total
        else:
            self.track_class_scores[track_id][label] += weight

        self.track_class_counts[track_id][label] += 1

        self.track_last_seen[track_id] = frame_index

        # --------------------------------------------------------
        # Find stable class
        # --------------------------------------------------------
        scores = self.track_class_scores[track_id]

        counts = self.track_class_counts[track_id]

        stable_label = max(
            scores,
            key=scores.get
        )

        total_score = sum(scores.values())

        if total_score > 0:
            stability = (
                scores[stable_label] /
                total_score
            )
        else:
            stability = 0.0

        total_observations = sum(
            counts.values()
        )

        # --------------------------------------------------------
        # Return stable classification
        # --------------------------------------------------------
        return {
            **self._classification_presentation(track_id),
            "label": stable_label,

            # This is consistency/evidence share.
            # It should not be interpreted as calibrated
            # ConvNeXt probability.
            "stability": round(
                float(stability),
                4
            ),

            "observations": int(
                total_observations
            ),

            # Latest frame prediction
            "current_label": label,

            "current_confidence": round(
                confidence,
                4
            ),

            "model": classification.get(
                "model",
                "ConvNeXt-Tiny"
            ),
        }

    # ============================================================
    # RESET VIDEO STATE
    # ============================================================

    def _reset_video_state(self):
        """
        Reset tracker and temporal classification state
        before processing a new video.

        The current VesselTracker implementation does not
        provide a reset() method, so its internal track
        dictionary and ID counter are reset directly.
        """

    # --------------------------------------------------------
    # Reset tracker
    # --------------------------------------------------------
        self.tracker.reset()
        self.camera_motion = CameraMotionEstimator()

    # --------------------------------------------------------
    # Reset temporal classification history
    # --------------------------------------------------------
        self.track_class_scores.clear()

        self.track_class_counts.clear()

        self.track_last_seen.clear()

        self.track_vlm_cache.clear()
        self.track_vlm_attempts = {}

        # --------------------------------------------------------
        # Reset RL adaptive compute scheduler state
        # --------------------------------------------------------
        if hasattr(self, "scheduler") and hasattr(self.scheduler, "reset"):
            self.scheduler.reset()

    # ============================================================
    # IOU
    # ============================================================

    @staticmethod
    def _calculate_iou(box_a, box_b):
        """
        Calculate IoU between two HBB boxes.

        box format:
            [x1, y1, x2, y2]
        """

        ax1, ay1, ax2, ay2 = map(
            float,
            box_a
        )

        bx1, by1, bx2, by2 = map(
            float,
            box_b
        )

        intersection_x1 = max(
            ax1,
            bx1
        )

        intersection_y1 = max(
            ay1,
            by1
        )

        intersection_x2 = min(
            ax2,
            bx2
        )

        intersection_y2 = min(
            ay2,
            by2
        )

        intersection_width = max(
            0.0,
            intersection_x2 - intersection_x1
        )

        intersection_height = max(
            0.0,
            intersection_y2 - intersection_y1
        )

        intersection_area = (
            intersection_width *
            intersection_height
        )

        area_a = max(
            0.0,
            ax2 - ax1
        ) * max(
            0.0,
            ay2 - ay1
        )

        area_b = max(
            0.0,
            bx2 - bx1
        ) * max(
            0.0,
            by2 - by1
        )

        union_area = (
            area_a +
            area_b -
            intersection_area
        )

        if union_area <= 0:
            return 0.0

        return (
            intersection_area /
            union_area
        )

    # ============================================================
    # FILTER DETECTIONS
    # ============================================================

    def _filter_detections(
        self,
        detections,
        confidence_threshold=0.25,
        iou_threshold=0.60,
    ):
        """
        Remove low-confidence and duplicate detections.
        """

        if not detections:
            return []

        # --------------------------------------------------------
        # Confidence filtering
        # --------------------------------------------------------
        detections = [
            detection
            for detection in detections
            if float(
                detection.get(
                    "confidence",
                    0.0
                )
            ) >= confidence_threshold
        ]

        # --------------------------------------------------------
        # Highest confidence first
        # --------------------------------------------------------
        detections = sorted(
            detections,
            key=lambda d: float(
                d.get(
                    "confidence",
                    0.0
                )
            ),
            reverse=True,
        )

        # --------------------------------------------------------
        # Non-Maximum Suppression style duplicate removal
        # --------------------------------------------------------
        filtered = []

        for detection in detections:

            bbox = detection.get(
                "bbox"
            )

            if not bbox:
                continue

            duplicate = False

            for selected in filtered:

                selected_bbox = selected.get(
                    "bbox"
                )

                if not selected_bbox:
                    continue

                iou = self._calculate_iou(
                    bbox,
                    selected_bbox
                )

                if iou > iou_threshold:
                    duplicate = True
                    break

            if not duplicate:
                filtered.append(
                    detection
                )

        return filtered

    # ============================================================
    # SCENE COMPLEXITY
    # ============================================================

    @staticmethod
    def _calculate_scene_complexity(
        detections,
        frame_width=None,
        frame_height=None,
    ):
        """
        Estimate scene complexity from the number and size
        of detected vessels.

        This is currently used by the rule-based scheduler.

        It is NOT a trained PPO policy yet.
        """

        if not detections:
            return 0.0

        count_score = min(
            len(detections) / 10.0,
            1.0
        )

        size_score = 0.0

        if frame_width and frame_height:

            frame_area = (
                frame_width *
                frame_height
            )

            if frame_area > 0:

                total_area = 0.0

                for detection in detections:

                    bbox = detection.get(
                        "bbox"
                    )

                    if not bbox:
                        continue

                    x1, y1, x2, y2 = map(
                        float,
                        bbox
                    )

                    width = max(
                        0.0,
                        x2 - x1
                    )

                    height = max(
                        0.0,
                        y2 - y1
                    )

                    total_area += (
                        width *
                        height
                    )

                size_score = min(
                    total_area /
                    frame_area,
                    1.0
                )

        complexity = (
            0.7 * count_score +
            0.3 * size_score
        )

        return min(
            max(
                complexity,
                0.0
            ),
            1.0
        )

    # ============================================================
    # TRACK / DETECTION MATCHING
    # ============================================================

    @staticmethod
    def _center_distance(
        track,
        detection,
    ):
        """
        Euclidean distance between tracker center and
        detector center.
        """

        dx = (
            float(track["cx"]) -
            float(detection["cx"])
        )

        dy = (
            float(track["cy"]) -
            float(detection["cy"])
        )

        return (
            dx * dx +
            dy * dy
        ) ** 0.5

    def _match_track_to_detection(
        self,
        track,
        detections,
        max_distance=100.0,
    ):
        """
        Return the exact one-to-one detector association made by the tracker.

        Older tracker outputs do not contain this association, so retain the
        nearest-centre fallback for backwards compatibility.  New outputs
        must never fall back: a track that was merely predicted this frame
        has no current crop to classify.
        """

        if "matched_detection" in track:
            return track.get("matched_detection")

        if not detections:
            return None

        best_detection = None

        best_distance = float(
            "inf"
        )

        for detection in detections:

            distance = self._center_distance(
                track,
                detection
            )

            if distance < best_distance:

                best_distance = distance

                best_detection = detection

        if (
            best_detection is not None
            and best_distance <= max_distance
        ):
            return best_detection

        return None

    # ============================================================
    # CLASSIFY TRACK
    # ============================================================

    def _classify_track(
        self,
        track,
        detection,
        frame_index=None,
    ):
        """
        Crop the detected vessel, classify it, and update
        temporal Track ID classification.
        """
        if detection is None:
            return None, None

        bbox = detection.get("bbox")
        if not bbox:
            return None, None

        try:
            source = getattr(self, "_current_frame", None)
            if source is None:
                source = getattr(self, "_current_image_path", None)

            track_id = int(track["track_id"])

            crop = self.detector.crop(source, bbox)
            hits = track.get("hits", 1)
            # One successful reasoning event per track, scoped to this video reset.
            # Local classification still supplies a fresh vote on each observation.
            classification = self.classifier.classify(crop, vlm=None, use_vlm_disambiguation=False)
            cached = self.track_vlm_cache.get(track_id)
            if not hasattr(self, "track_vlm_attempts"):
                self.track_vlm_attempts = {}
            import time
            now = time.monotonic()
            interval = max(1.0, float(os.getenv("GROQ_TRACK_RETRY_SECONDS", "60")))
            enabled = getattr(self, "video_vlm_enabled", True)
            uncertain = classification.get("uncertain") or classification.get("margin", 1) < 0.25
            if cached:
                self.vlm.guard.track_cache_hit()
                classification["vlm"] = {**cached, "source": "cached"}
            elif enabled and hits >= 3 and uncertain:
                last_attempt = self.track_vlm_attempts.get(track_id, float("-inf"))
                result = None
                if now-last_attempt >= interval:
                    self.track_vlm_attempts[track_id] = now
                    result = self.vlm.classify_vessel(crop)
                if result:
                    source = self.vlm.guard.last_source
                    self.track_vlm_cache[track_id] = result
                    classification["vlm"] = {**result, "source": source}
                    # Reasoning is advisory metadata; local classifier probabilities
                    # remain the observation used for temporal aggregation.
                else:
                    classification["vlm"] = {"source": "unavailable", "fallback": "ConvNeXt-Tiny"}
            else:
                classification["vlm"] = {"source": "not_requested" if enabled else "disabled"}

            classification["detector_confidence"] = detection.get("confidence",1.)
            if hasattr(source,"shape"):
                x1,y1,x2,y2=map(float,bbox);height,width=source.shape[:2]
                visible=max(0,min(width,x2)-max(0,x1))*max(0,min(height,y2)-max(0,y1))
                classification["crop_quality_weight"] = visible/max(1.,(x2-x1)*(y2-y1))
            stable_classification = self._update_track_classification(
                track_id,
                classification,
                frame_index
            )

            return classification, stable_classification

        except Exception as exc:
            print(f"[WARN] Classification failed for Track {track.get('track_id')}: {exc}")
            return None, None

    def _classification_presentation(self, track_id):
        scores = self.track_class_scores.get(track_id, {})
        if not scores:
            return {}
        ordered = sorted(scores, key=scores.get, reverse=True)
        total = sum(scores.values()) or 1.
        best = ordered[0]
        share = scores[best]/total
        runner = ordered[1] if len(ordered)>1 else None
        margin = share-(scores[runner]/total if runner else 0.)
        observations = sum(self.track_class_counts.get(track_id, {}).values())
        uncertain = observations < 3 or share < .55 or margin < .25
        pair = {best, runner} == {"Frigate", "Destroyer"}
        display = ("Frigate / Destroyer (uncertain)" if pair else f"{best} (unverified)") if uncertain else f"{best} (model estimate)"
        return {"display_label": display, "uncertain": uncertain,
                "classification_status": "uncertain" if uncertain else "model_estimate",
                "candidates": [{"label": name, "evidence_share": round(scores[name]/total,4)} for name in ordered[:2]]}

    def _stable_track_classification(self, track_id):
        """Read persistent evidence without adding fake votes during coasting."""
        scores=self.track_class_scores.get(track_id,{})
        if not scores: return None
        label=max(scores,key=scores.get); total=sum(scores.values())
        return {"label":label,"stability":round(scores[label]/total,4),
                "observations":sum(self.track_class_counts.get(track_id,{}).values()),
                **self._classification_presentation(track_id)}

    # ============================================================
    # SATELLITE IMAGE
    # ============================================================

    # ============================================================
    # SATELLITE IMAGE
    # ============================================================

    def satellite_detect(
        self,
        image_path,
        imgsz=1024,
        weights=None,
        conf=0.25,
        iou=0.60,
    ):
        """
        Satellite mode:
            Satellite image -> High-resolution YOLO detection (imgsz=1024) -> Bounding box annotation -> Groq VLM briefing
        """
        image_path = str(Path(image_path))

        if weights:
            self.detector.load_model(weights)

        conf_val = float(conf) if conf is not None else 0.25
        iou_val = float(iou) if iou is not None else 0.60

        # Always run high resolution on wide satellite imagery
        detections = self.detector.predict(image_path, mode="satellite", imgsz=imgsz, conf=conf_val, iou=iou_val)
        detections = self._filter_detections(detections, confidence_threshold=conf_val, iou_threshold=iou_val)

        # Draw bounding boxes on satellite image
        annotated_path = None
        try:
            img = cv2.imread(image_path)
            if img is not None:
                img_h, img_w = img.shape[:2]
                annotated_img = img.copy()

                for i, det in enumerate(detections, start=1):
                    bbox = det.get("bbox", [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(img_w - 1, x2), min(img_h - 1, y2)

                        conf_score = float(det.get("confidence", 0.0))
                        label_txt = f"Vessel #{i}: {conf_score * 100:.1f}%"

                        # Draw box: crisp cyan/green with 2px stroke
                        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 240, 160), 2)

                        # Badge background
                        font_scale = 0.55
                        thickness = 1
                        (tw, th), _ = cv2.getTextSize(label_txt, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                        badge_y = max(th + 6, y1 - 6)
                        cv2.rectangle(annotated_img, (x1, badge_y - th - 4), (x1 + tw + 6, badge_y + 4), (16, 22, 34), -1)
                        cv2.rectangle(annotated_img, (x1, badge_y - th - 4), (x1 + tw + 6, badge_y + 4), (0, 240, 160), 1)
                        cv2.putText(annotated_img, label_txt, (x1 + 3, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 230), thickness, cv2.LINE_AA)

                # Save annotated satellite image
                stem = Path(image_path).stem
                out_dir = Path("data/results")
                out_dir.mkdir(parents=True, exist_ok=True)
                annotated_path = out_dir / f"annotated_satellite_{stem}.jpg"
                cv2.imwrite(str(annotated_path), annotated_img)

                # Also mirror to outputs/predictions
                out_dir2 = Path("outputs/predictions")
                out_dir2.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_dir2 / f"annotated_satellite_{stem}.jpg"), annotated_img)
        except Exception as exc:
            print(f"[WARN] Failed to generate annotated satellite image: {exc}")

        try:
            briefing = self.vlm.generate_briefing(
                image_path,
                detections,
                mode="satellite"
            )
        except Exception as exc:
            briefing = f"VLM analysis unavailable: {exc}"

        return {
            "status": "success",
            "mode": "satellite",
            "image_path": image_path,
            "annotated_image_path": str(annotated_path) if annotated_path and annotated_path.exists() else None,
            "ship_count": len(detections),
            "detections": detections,
            "model_variant": getattr(self.detector, "model_name", "YOLO11n-VHRV Detector"),
            "weights_used": getattr(self.detector, "satellite_weights", "models/weights/vhrv_best.pt"),
            "conf_threshold": conf_val,
            "iou_threshold": iou_val,
            "vlm_analysis": briefing,
        }

    # ============================================================
    # DRONE VIDEO
    # ============================================================

    def drone_video(
        self,
        video_path,
        target_x=0.0,
        target_y=0.0,
        sample_every=1,
        max_frames=None,
        original_name=None,
        use_ppo=True,
        output_dir=None,
        write_analytics=True,
        vlm_enabled=True,
    ):
        """
        Process an MP4 video frame-by-frame with real PPO-based adaptive compute:
        - LOW:    Sample every 4th frame (conserves compute on empty water)
        - NORMAL: Sample every 2nd frame (standard tactical cruise)
        - HIGH:   Sample every frame (high-activity tactical encounters)
        - Safety Override: Automatically bumps to NORMAL/HIGH if sudden target appears
        """
        video_path = str(Path(video_path))
        self._reset_video_state()
        self.video_vlm_enabled = vlm_enabled

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "status": "error",
                "message": f"Could not open video: {video_path}",
            }

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Setup H.264 Video Writer for browser playback
        results_dir = Path(output_dir) if output_dir else Path("data/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        videos_dir = results_dir if output_dir else Path("outputs/videos")
        videos_dir.mkdir(parents=True, exist_ok=True)

        video_stem = Path(video_path).stem
        safe_stem = "".join(c for c in video_stem if c.isalnum() or c in ("-", "_")).strip() or "drone_video"
        run_id = uuid4().hex[:12]
        annotated_video_path = results_dir / f"annotated_{safe_stem}_{run_id}.mp4"
        copy_video_path = videos_dir / annotated_video_path.name
        diagnostic_path = (results_dir if output_dir else Path("outputs/diagnostics")) / f"tracking_{safe_stem}_{run_id}.csv"
        diagnostic_log = TrackingDiagnosticCSV(diagnostic_path)

        video_writer = None
        try:
            import imageio_ffmpeg
            effective_fps = fps / max(1, sample_every)
            video_writer = imageio_ffmpeg.write_frames(
                str(annotated_video_path),
                size=(frame_width, frame_height),
                fps=effective_fps,
                codec="libx264",
                pix_fmt_in="bgr24",
                pix_fmt_out="yuv420p",
                ffmpeg_log_level="error"
            )
            video_writer.send(None)
        except Exception as vw_err:
            print(f"[WARN] VideoWriter init failed: {vw_err}")
            video_writer = None

        frame_results = []
        processed_frames = 0
        total_detections = 0
        total_yolo_calls = 0
        total_classifier_calls = 0
        total_compute_cost = 0.0
        safety_overrides_count = 0
        processing_modes = Counter()
        track_history = defaultdict(list)
        recent_detection_counts = []
        last_known_detections = []

        frame_index = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if sample_every > 1 and frame_index % sample_every != 0:
                frame_index += 1
                continue

            if max_frames is not None and processed_frames >= max_frames:
                break

            processed_frames += 1

            try:
                camera = self.camera_motion.update(frame, [t.bbox for t in self.tracker.tracks.values()])
                if camera['scene_cut']:
                    self.scheduler.reset()
                    # IDs remain monotonic across cuts: archive old classification
                    # evidence for the registry, never transfer it into a new ID.
                    track_history.clear()
                    recent_detection_counts.clear(); last_known_detections = []
                # --------------------------------------------------------
                # PPO Adaptive Compute Decision
                # --------------------------------------------------------
                active_confirmed = [
                    t for t in self.tracker.tracks.values()
                    if t.confirmed_at is not None and t.seconds_since_measurement <= self.tracker.recent_seconds
                ]
                recent_avg_dets = (
                    float(sum(recent_detection_counts[-10:]) / len(recent_detection_counts[-10:]))
                    if recent_detection_counts else 0.0
                )
                recent_confs = [float(d.get("confidence", 0.0)) for d in last_known_detections]
                avg_conf = float(sum(recent_confs) / len(recent_confs)) if recent_confs else 0.0
                target_vis = (len(recent_detection_counts) > 0 and recent_detection_counts[-1] > 0)

                obs = self.scheduler.build_observation(
                    target_visible=target_vis,
                    detection_count=recent_detection_counts[-1] if recent_detection_counts else 0,
                    active_track_count=len(active_confirmed),
                    avg_confidence=avg_conf,
                    frame_progress=frame_index / max(1, frame_count),
                )

                ppo_action, processing_mode, safety_override = self.scheduler.select_action(obs) if use_ppo else (2, "heavy", False)
                if camera['scene_cut'] or processed_frames == 1:
                    ppo_action, processing_mode, safety_override = 2, "heavy", True
                elif any(t.state == "lost" for t in self.tracker.tracks.values()) and ppo_action == 0:
                    ppo_action, processing_mode, safety_override = 1, "standard", True
                if safety_override:
                    safety_overrides_count += 1
                processing_modes[processing_mode] += 1

                # Cost factor based on PPO action
                cost_factor = 0.25 if ppo_action == 0 else (0.50 if ppo_action == 1 else 1.00)
                total_compute_cost += cost_factor

                # PPO controls whether detector runs this frame:
                if ppo_action == 2:      # HIGH: every frame
                    should_detect = True
                elif ppo_action == 1:    # NORMAL: every 2nd frame
                    should_detect = (processed_frames % 2 == 0)
                else:                    # LOW: every 4th frame
                    should_detect = (processed_frames % 4 == 0)

                yolo_called = False
                if should_detect:
                    self._current_frame = frame
                    self._current_image_path = None
                    detections = self.detector.predict(frame, mode="drone", conf=0.18, iou=0.45)
                    detections = self._filter_detections(detections, confidence_threshold=0.18, iou_threshold=0.50)
                    total_yolo_calls += 1
                    yolo_called = True
                    last_known_detections = detections
                else:
                    detections = []
                    yolo_called = False

                if yolo_called:
                    recent_detection_counts.append(len(detections))
                self.camera_motion.exclude_current_boxes([d['bbox'] for d in detections], frame_width)
                total_detections += len(detections)

                # Tracker update (coasts smoothly if detections is empty)
                tracks = self.tracker.update(detections, timestamp=frame_index/fps,
                    inference_ran=yolo_called, camera_transform=camera['affine'],
                    scene_cut=camera['scene_cut'], include_predictions=True, camera_status=camera['status'])
                diagnostic_log.write(frame_index,frame_index/fps,self.tracker.last_diagnostics,ppo_action)
                track_results = []
                classifier_called_this_frame = False

                for track in tracks:
                    detection = self._match_track_to_detection(track, detections)
                    current_classification = None
                    stable_classification = self._stable_track_classification(track["track_id"])

                    # Classify if detection was made and track is confirmed
                    if detection is not None:
                        # Throttled classification based on PPO mode
                        should_classify = (
                            ppo_action == 2 or
                            (ppo_action == 1 and processed_frames % 4 == 0) or
                            (track.get("hits", 0) <= 3)
                        )
                        if should_classify:
                            (
                                current_classification,
                                stable_classification,
                            ) = self._classify_track(track, detection, frame_index)
                            total_classifier_calls += 1
                            classifier_called_this_frame = True

                    track_result = {
                        **track,
                        "track_id": track["track_id"],
                        "cx": track["cx"],
                        "cy": track["cy"],
                        "w": track["w"],
                        "h": track["h"],
                        "confidence": track["confidence"],
                        "missed": track["missed"],
                        "age": track["age"],
                        "state": track.get("state", "confirmed"),
                        "detection_index": track.get("detection_index"),
                        "detection_bbox": (
                            track.get("matched_detection", {}) or {}
                        ).get("bbox"),
                        "classification": current_classification,
                        "classification_stable": stable_classification,
                    }
                    track_results.append(track_result)

                if video_writer is not None:
                    annotated_frame=draw_tracking(frame,track_results,self.tracker.last_diagnostics,
                                                  frame_index,processing_mode,safety_override)
                    video_writer.send(annotated_frame)

                frame_result = {
                    "frame_index": frame_index,
                    "timestamp": frame_index / fps,
                    "detections": detections,
                    "tracks": track_results,
                    "ship_count": len(detections),
                    "tracking_diagnostics": self.tracker.last_diagnostics,
                    "active_track_count": len(tracks),
                    "confirmed_track_count": self.tracker.last_diagnostics['confirmed_tracks'],
                    "coasting_track_count": self.tracker.last_diagnostics['coasting_tracks'],
                    "recovered_track_count": self.tracker.last_diagnostics['recovered_tracks'],
                    "scene_cut": camera['scene_cut'],
                    "camera_motion_status": camera['status'],
                    "camera_motion": {k:v for k,v in camera.items() if k != 'affine'},
                    "processing_mode": processing_mode,
                    "ppo_action": ppo_action,
                    "yolo_called": yolo_called,
                    "classifier_called": classifier_called_this_frame,
                    "compute_cost": cost_factor,
                    "safety_override": safety_override,
                }
                frame_results.append(frame_result)

            except Exception as exc:
                frame_results.append({
                    "frame_index": frame_index,
                    "timestamp": frame_index / fps,
                    "detections": [],
                    "tracks": [],
                    "ship_count": 0,
                    "active_track_count": 0,
                    "processing_mode": "error",
                    "error": str(exc),
                })
                print(f"[WARN] Frame {frame_index} failed: {exc}")
                if video_writer is not None:
                    error_frame=frame.copy()
                    cv2.putText(error_frame,"Processing error - tracking unavailable",(10,30),cv2.FONT_HERSHEY_SIMPLEX,.6,(60,60,255),2)
                    video_writer.send(error_frame)

            frame_index += 1

        cap.release()
        diagnostic_log.close()
        if video_writer is not None:
            try:
                video_writer.close()
                if annotated_video_path.exists() and annotated_video_path != copy_video_path:
                    shutil.copy2(str(annotated_video_path), str(copy_video_path))
            except Exception:
                pass

        # Summarize unique tracks and evidence
        unique_track_ids = set()
        for fr in frame_results:
            for tr in fr.get("tracks", []):
                unique_track_ids.add(tr["track_id"])

        final_track_classifications = {}
        track_summaries = {}
        last_tracking = {}
        last_measurement_frames = {}
        for fr in frame_results:
            for tr in fr.get('tracks', []):
                last_tracking[tr['track_id']] = tr
                if tr.get('observed', True): last_measurement_frames[tr['track_id']] = fr['frame_index']
            for tr in fr.get('tracking_diagnostics', {}).get('deleted_tracks', []):
                last_tracking[tr['track_id']] = tr

        for track_id in unique_track_ids:
            scores = self.track_class_scores.get(track_id, {})
            counts = self.track_class_counts.get(track_id, {})
            if not scores:
                continue

            stable_label = max(scores, key=scores.get)
            total_score = sum(scores.values())
            stability = scores[stable_label] / total_score if total_score > 0 else 0.0
            observations = sum(counts.values())

            final_track_classifications[track_id] = {
                "label": stable_label,
                "stability": round(float(stability), 4),
                "observations": int(observations),
            }

            track_summaries[str(track_id)] = {
                "vlm": ({**self.track_vlm_cache[track_id], "source": "cached"}
                        if track_id in self.track_vlm_cache else {"source": "disabled" if not self.video_vlm_enabled else ("unavailable" if track_id in self.track_vlm_attempts else "not_requested")}),
                "track_id": int(track_id),
                "label": stable_label,
                "stability": round(float(stability), 4),
                "observations": int(observations),
                "last_seen_frame": self.track_last_seen.get(track_id),
                "last_measurement_frame": last_measurement_frames.get(track_id),
                "tracking_state": last_tracking.get(track_id, {}).get('state'),
                "lifecycle_state": last_tracking.get(track_id, {}).get('lifecycle_state'),
                "classification_status": (
                    "confirmed"
                    if observations >= 2 and stability >= 0.50
                    else "limited_evidence"
                ),
                **self._classification_presentation(track_id),
            }

        track_summaries, track_state_counts = build_track_registry(frame_results, track_summaries)

        primary_vessel = None
        if track_summaries:
            primary_vessel = max(
                track_summaries.values(),
                key=lambda item: (
                    item["observations"] * item["stability"],
                    item["observations"],
                ),
            )

        average_detections = (
            total_detections / processed_frames if processed_frames > 0 else 0.0
        )
        status_message = (
            "ship activity detected" if total_detections > 0 else "no ship detected"
        )

        has_annotated = annotated_video_path.exists() and annotated_video_path.stat().st_size > 1000

        # Estimated compute reduction calculation (proxy for edge energy)
        max_possible_compute = max(1.0, float(processed_frames))
        compute_reduction_pct = round((1.0 - total_compute_cost / max_possible_compute) * 100, 2)

        # --------------------------------------------------------
        # Dynamically record mission into PPO Multi-Scenario Benchmark
        # --------------------------------------------------------
        scenario_clean_name = original_name or Path(video_path).name
        primary_label = primary_vessel.get("label", "Maritime Vessel") if primary_vessel else "Maritime Vessel"
        
        # Scan mode label
        scan_mode_label = f"{fps/max(1,sample_every):g} FPS / sample 1/{sample_every}"
        if max_frames:
            scan_mode_label += f" ({max_frames}f Preview)"

        # Canonical scenario key mapping to avoid conflicting duplicate benchmark rows
        lower_name = scenario_clean_name.lower()
        if "oil_tanker" in lower_name or "oil tanker" in lower_name:
            scenario_key = "Oil Tanker Surveillance (oil_tanker_drone.mp4)"
            benchmark_canonical_key = "Oil Tanker Surveillance"
        elif "cruise" in lower_name or "allure" in lower_name:
            scenario_key = "Cruise Ship Surveillance (cruise_ship_drone.mp4)"
            benchmark_canonical_key = "Cruise Ship Surveillance"
        elif "test1" in lower_name or "kasturi" in lower_name or "frigate" in primary_label.lower():
            scenario_key = "Frigate Surveillance (KD Kasturi F25 - test1.mp4)"
            benchmark_canonical_key = "Frigate Surveillance (KD Kasturi F25)"
        elif "test2" in lower_name or "amphibious" in lower_name:
            scenario_key = "Amphibious assault ship Surveillance (test2.mp4)"
            benchmark_canonical_key = "Amphibious assault ship Surveillance (test2.mp4)"
        elif "test3" in lower_name or "destroyer" in lower_name:
            scenario_key = "Destroyer Surveillance (test3.mp4)"
            benchmark_canonical_key = "Destroyer Surveillance (test3.mp4)"
        else:
            scenario_key = f"{primary_label} Surveillance ({scenario_clean_name})"
            benchmark_canonical_key = scenario_key

        new_benchmark_record = {
            "total_frames": processed_frames,
            "scan_mode": scan_mode_label,
            "full_processing": {
                "frames_processed": processed_frames,
                "yolo_calls": processed_frames,
                "estimated_compute_cost": float(processed_frames),
                "estimated_compute_reduction_pct": 0.0,
            },
            "ppo_adaptive_scheduler": {
                "frames_processed": processed_frames,
                "scan_mode": scan_mode_label,
                "yolo_calls": total_yolo_calls,
                "estimated_compute_cost": round(total_compute_cost, 1),
                "estimated_compute_reduction_pct": compute_reduction_pct,
                "action_distribution": {
                    "0": processing_modes.get("lightweight", 0),
                    "1": processing_modes.get("standard", 0),
                    "2": processing_modes.get("heavy", 0),
                },
                "safety_overrides_triggered": safety_overrides_count,
                "identified_vessel": primary_label,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

        if write_analytics:
            # Update persistent outputs/rl/scheduler_comparison_metrics.json cleanly
            rl_dir = Path("outputs/rl")
            rl_dir.mkdir(parents=True, exist_ok=True)
            bench_file = rl_dir / "scheduler_comparison_metrics.json"

            bench_data = {}
            if bench_file.exists():
                try:
                    with open(bench_file, "r") as bf:
                        bench_data = json.load(bf)
                except Exception:
                    bench_data = {}

            # Retain rule-based scheduler metrics if already present in canonical entry
            if benchmark_canonical_key in bench_data and "rule_based_scheduler" in bench_data[benchmark_canonical_key]:
                new_benchmark_record["rule_based_scheduler"] = bench_data[benchmark_canonical_key]["rule_based_scheduler"]

            # Clean up any legacy duplicate aliases
            for legacy_k in [
                "Oil tanker Surveillance (oil_tanker_drone.mp4)",
                "Frigate Tactical Patrol (KD Kasturi F25)",
                "Frigate Surveillance (KD Kasturi F25 - test1.mp4)"
            ]:
                if legacy_k != benchmark_canonical_key and legacy_k in bench_data:
                    bench_data.pop(legacy_k, None)

            bench_data[benchmark_canonical_key] = new_benchmark_record
            try:
                with open(bench_file, "w") as bf:
                    json.dump(bench_data, bf, indent=2)
            except Exception as b_err:
                print(f"[WARN] Failed to write scheduler benchmark: {b_err}")

            # Update live chronological mission log
            history_file = rl_dir / "live_mission_history.json"
            history_list = []
            if history_file.exists():
                try:
                    with open(history_file, "r") as hf:
                        history_list = json.load(hf)
                except Exception:
                    history_list = []

            history_list.append({
                "scenario": scenario_key,
                "video_file": scenario_clean_name,
                "scan_mode": scan_mode_label,
                "vessel_class": primary_label,
                "evidence_stability": (
                    f"{primary_vessel.get('stability', 0.0)*100:.1f}%"
                    if primary_vessel else "N/A"
                ),
                "total_frames": processed_frames,
                "compute_cost": round(total_compute_cost, 1),
                "compute_saved_pct": f"{compute_reduction_pct:.1f}%",
                "modes": (
                    f"LOW: {processing_modes.get('lightweight', 0)} | "
                    f"NORM: {processing_modes.get('standard', 0)} | "
                    f"HIGH: {processing_modes.get('heavy', 0)}"
                ),
                "safety_overrides": safety_overrides_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            try:
                with open(history_file, "w") as hf:
                    json.dump(history_list[-50:], hf, indent=2)
            except Exception as h_err:
                print(f"[WARN] Failed to write mission history: {h_err}")

        return {
            "status": "success",
            "mode": "drone_video",
            "scan_mode": scan_mode_label,
            "tracking_diagnostic_csv": str(diagnostic_path),
            "detector_call_reduction_pct": round(100*(1-total_yolo_calls/max(1,processed_frames)),2),
            "vlm_service": self.vlm.availability(),
            "tracking_velocity_units": "pixels/second",
            "video_path": video_path,
            "scenario_name": scenario_key,
            "annotated_video_path": str(annotated_video_path) if has_annotated else None,
            "fps": fps,
            "frame_count": frame_count,
            "processed_frames": processed_frames,
            "resolution": {
                "width": frame_width,
                "height": frame_height,
            },
            "status_message": status_message,
            "unique_track_count": len(unique_track_ids),
            "total_detections": total_detections,
            "average_detections_per_frame": round(average_detections, 4),
            "processing_mode_counts": dict(processing_modes),
            "final_track_classifications": final_track_classifications,
            "track_state_counts": track_state_counts,
            "track_summaries": track_summaries,
            "primary_vessel": primary_vessel,
            "yolo_calls": total_yolo_calls,
            "classifier_calls": total_classifier_calls,
            "estimated_compute_cost": round(total_compute_cost, 2),
            "estimated_compute_reduction": compute_reduction_pct,
            "safety_overrides": safety_overrides_count,
            "frames": frame_results,
        }


