"""
tests/test_kalman_tracker.py
Unit and Integration Test Suite for the Modular Kalman-Filter Vessel Tracker.

Verifies:
1. Kalman Prediction (state propagation over constant velocity motion)
2. Kalman Measurement Update (covariance reduction and state correction)
3. Track Creation (initialization, tentative state)
4. Track Persistence (consistent ID across continuous movement)
5. Missed Detections (coasting through dropped frames and re-acquisition)
6. Track Deletion (pruning dead tracks after max_missed threshold)
7. Multiple Vessels (adjacent ships retain distinct identities)
8. ID Consistency (prevention of ID switching under occlusion)
"""
import math
import numpy as np
import pytest

from tracking.kalman_filter import KalmanFilter
from tracking.track import Track
from tracking.kalman_tracker import KalmanTracker
from tracking.association import bbox_iou, size_similarity, compute_association_cost


def test_kalman_filter_prediction():
    """Verify state propagation under constant velocity motion."""
    kf = KalmanFilter()
    # Initialize vessel at (100, 100) with size (50, 20)
    kf.initialize(np.array([100.0, 100.0, 50.0, 20.0]))
    
    # Simulate movement: update with position (110, 105)
    kf.predict()
    kf.update(np.array([110.0, 105.0, 50.0, 20.0]))
    
    vx, vy = kf.velocity
    assert vx > 0.0, f"Expected positive vx, got {vx}"
    assert vy > 0.0, f"Expected positive vy, got {vy}"
    
    # Predict without update
    pred_x = kf.predict()
    cx, cy = kf.centroid
    assert cx > 110.0, f"Expected cx to advance beyond 110, got {cx}"
    assert cy > 105.0, f"Expected cy to advance beyond 105, got {cy}"


def test_kalman_filter_measurement_update():
    """Verify covariance reduction and smooth measurement convergence."""
    kf = KalmanFilter()
    kf.initialize(np.array([200.0, 300.0, 80.0, 40.0]))
    initial_p_trace = np.trace(kf.P[:4, :4])
    
    kf.predict()
    kf.update(np.array([205.0, 302.0, 80.0, 40.0]))
    updated_p_trace = np.trace(kf.P[:4, :4])
    
    assert updated_p_trace < initial_p_trace, "Covariance trace must decrease after measurement update"
    cx, cy = kf.centroid
    assert 200.0 < cx <= 205.0
    assert 300.0 < cy <= 302.0


def test_track_creation():
    """Verify instantiation, initial attributes, and tentative state."""
    det = {"cx": 150.0, "cy": 250.0, "w": 40.0, "h": 20.0, "confidence": 0.88}
    track = Track(track_id=1, detection=det)
    
    assert track.track_id == 1
    assert track.age == 1
    assert track.hits == 1
    assert track.missed_frames == 0
    assert track.tracking_state == Track.STATE_TENTATIVE
    assert track.confidence == 0.88
    assert math.isclose(track.cx, 150.0, abs_tol=1e-2)
    assert math.isclose(track.cy, 250.0, abs_tol=1e-2)
    
    d = track.to_dict()
    assert d["track_id"] == 1
    assert "bbox" in d
    assert "bounding_box" in d
    assert "centroid" in d


def test_track_persistence():
    """Verify track maintains consistent ID over continuous observations."""
    tracker = KalmanTracker()
    
    # Vessel sails along diagonal path: cx += 5, cy += 2
    for frame_idx in range(10):
        det = {
            "cx": 100.0 + frame_idx * 5.0,
            "cy": 200.0 + frame_idx * 2.0,
            "w": 50.0,
            "h": 25.0,
            "confidence": 0.92,
        }
        active_tracks = tracker.update([det])
        assert len(active_tracks) == 1
        assert active_tracks[0]["track_id"] == 1
        
        # After 2 hits, track should be confirmed
        if frame_idx >= 1:
            assert active_tracks[0]["state"] == Track.STATE_CONFIRMED


def test_missed_detection_coasting_and_recovery():
    """Verify Kalman coasting during temporary missed detections without losing ID."""
    tracker = KalmanTracker()
    
    # Frame 1: Initial detection
    det1 = {"cx": 100.0, "cy": 100.0, "w": 60.0, "h": 30.0, "confidence": 0.90}
    t1 = tracker.update([det1])
    assert len(t1) == 1
    assert t1[0]["track_id"] == 1
    
    # Frame 2: Second detection to confirm track
    det2 = {"cx": 106.0, "cy": 102.0, "w": 60.0, "h": 30.0, "confidence": 0.91}
    t2 = tracker.update([det2])
    assert len(t2) == 1
    assert t2[0]["track_id"] == 1
    assert t2[0]["state"] == Track.STATE_CONFIRMED
    
    # Frames 3 & 4: Detection dropped (cloud / occlusion / sea spray)
    t3 = tracker.update([])
    assert len(t3) == 0, "No measurement in frame 3, output should be empty"
    assert tracker.tracks[1].missed_frames == 1
    
    t4 = tracker.update([])
    assert len(t4) == 0
    assert tracker.tracks[1].missed_frames == 2
    
    # Frame 5: Vessel re-detected near Kalman-predicted location
    det5 = {"cx": 124.0, "cy": 108.0, "w": 60.0, "h": 30.0, "confidence": 0.87}
    t5 = tracker.update([det5])
    assert len(t5) == 1
    # MUST retain the exact same track ID 1
    assert t5[0]["track_id"] == 1
    assert tracker.tracks[1].missed_frames == 0
    assert tracker.tracks[1].tracking_state == Track.STATE_CONFIRMED


def test_track_deletion():
    """Verify track is pruned once consecutive missed frames exceed max_missed."""
    tracker = KalmanTracker(max_missed=5)
    det = {"cx": 50.0, "cy": 50.0, "w": 30.0, "h": 15.0, "confidence": 0.90}
    tracker.update([det])
    tracker.update([det])  # confirmed
    assert 1 in tracker.tracks
    
    # Miss 6 frames (exceeding max_missed=5)
    for _ in range(6):
        tracker.update([])
        
    assert 1 not in tracker.tracks, "Track must be deleted after exceeding max_missed"


def test_multiple_adjacent_vessels():
    """Verify distinct tracks are maintained for adjacent vessels in close proximity."""
    tracker = KalmanTracker()
    
    # Ship A and Ship B docked side-by-side
    ship_a = {"cx": 100.0, "cy": 100.0, "w": 30.0, "h": 80.0, "confidence": 0.95,
              "bbox": [85.0, 60.0, 115.0, 140.0]}
    ship_b = {"cx": 145.0, "cy": 100.0, "w": 30.0, "h": 80.0, "confidence": 0.92,
              "bbox": [130.0, 60.0, 160.0, 140.0]}
    
    t1 = tracker.update([ship_a, ship_b])
    assert len(t1) == 2
    assert t1[0]["track_id"] != t1[1]["track_id"]
    
    id_a = t1[0]["track_id"]
    id_b = t1[1]["track_id"]
    
    # Step forward slightly
    ship_a2 = {"cx": 102.0, "cy": 101.0, "w": 30.0, "h": 80.0, "confidence": 0.94,
               "bbox": [87.0, 61.0, 117.0, 141.0]}
    ship_b2 = {"cx": 147.0, "cy": 101.0, "w": 30.0, "h": 80.0, "confidence": 0.91,
               "bbox": [132.0, 61.0, 162.0, 141.0]}
    
    t2 = tracker.update([ship_a2, ship_b2])
    t2_ids = {tr["track_id"] for tr in t2}
    assert t2_ids == {id_a, id_b}, "Adjacent vessels must preserve their separate IDs"


def test_subpart_suppression():
    """Verify internal deck fittings or false detections inside hull do not spawn new tracks."""
    tracker = KalmanTracker()
    
    hull = {"cx": 200.0, "cy": 200.0, "w": 50.0, "h": 150.0, "confidence": 0.95,
            "bbox": [175.0, 125.0, 225.0, 275.0]}
    t1 = tracker.update([hull])
    assert len(t1) == 1
    
    # In frame 2, deck fitting detection appears inside hull
    fitting = {"cx": 202.0, "cy": 205.0, "w": 12.0, "h": 18.0, "confidence": 0.85,
               "bbox": [196.0, 196.0, 208.0, 214.0]}
    t2 = tracker.update([hull, fitting])
    assert len(t2) == 1, "Deck fitting inside vessel hull must be suppressed"
    assert t2[0]["track_id"] == 1
