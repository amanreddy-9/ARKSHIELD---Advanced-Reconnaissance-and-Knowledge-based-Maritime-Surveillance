"""Recorded diagnostics must reflect real association outcomes for presentation."""
import json
from tracking.kalman_tracker import KalmanTracker


def detection(confidence=0.9):
    return {"cx": 200.0, "cy": 100.0, "w": 60.0, "h": 20.0, "confidence": confidence}


def test_three_stage_diagnostics_and_state_serialization():
    tracker = KalmanTracker()
    tracker.update([detection()])
    first = tracker.last_diagnostics
    assert first["new_tracks"] == 1
    assert first["stage_matches"] == [0, 0, 0]
    tracker.update([detection()])
    assert tracker.last_diagnostics["stage_matches"] == [1, 0, 0]
    tracker.update([detection(0.2)])
    assert tracker.last_diagnostics["stage_matches"] == [0, 1, 0]
    for _ in range(4):
        tracker.update([])
    assert tracker.last_diagnostics["coasting_tracks"] == 1
    tracker.update([detection()])
    current = tracker.last_diagnostics
    assert current["stage_matches"] == [0, 0, 1]
    assert current["new_tracks"] == 0
    assert current["tracks"][0]["track_id"] == 1
    assert len(current["tracks"][0]["kalman_state"]) == 8
    assert len(current["tracks"][0]["covariance_diagonal"]) == 8
    json.dumps(current, allow_nan=False)
    assert first["new_tracks"] == 1
    tracker.reset()
    assert tracker.last_diagnostics == {}
