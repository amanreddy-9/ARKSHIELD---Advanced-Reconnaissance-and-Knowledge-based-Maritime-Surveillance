# tests/test_e2e_integration.py
"""
End-to-End Integration Test Suite for OATrack-VLM.
Tests detector, tracker, PPO scheduler, pipeline orchestrator, and backend endpoints.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from models.detector import VesselDetector
from models.classifier import ShipClassifier
from rl.scheduler import AdaptiveComputeScheduler
from tracking.tracker import VesselTracker
from pipeline.orchestrator import OATrackPipeline
from backend.main import app


def test_models_exist_and_load():
    """Verify all trained weight checkpoints exist and instantiate without error."""
    det = VesselDetector("models/weights/vhrv_best.pt")
    assert det.model is not None

    custom_p = Path("models/weights/vhrv_custom_best.pt")
    if custom_p.exists():
        det_custom = VesselDetector(str(custom_p))
        assert det_custom.model is not None

    cls = ShipClassifier()
    assert cls.model is not None

    sched = AdaptiveComputeScheduler("models/weights/ppo_scheduler.zip")
    assert sched.ppo_ready is True


def test_satellite_multi_ship_detection_quality():
    """Verify high-resolution detection on dense multi-ship satellite imagery."""
    img_path = Path("data/vhrv/vhrv/images/test/vhrv_01045.jpg")
    if not img_path.exists():
        pytest.skip("Test image vhrv_01045.jpg not found")

    pipeline = OATrackPipeline()
    res = pipeline.satellite_detect(str(img_path), imgsz=1024)

    assert res["status"] == "success"
    assert res["ship_count"] >= 5, f"Expected >= 5 ships in offshore convoy, found {res['ship_count']}"

    # Verify bounding boxes are well-formed (x2 > x1 and y2 > y1)
    for det in res["detections"][:15]:
        b = det["bbox"]
        assert len(b) == 4
        assert b[2] > b[0], "Invalid bbox width"
        assert b[3] > b[1], "Invalid bbox height"
        assert det["confidence"] >= 0.25

    # Verify annotated image was created and exists
    annot_path = res.get("annotated_image_path")
    assert annot_path is not None
    assert Path(annot_path).exists()


def test_adjacent_ship_separation_and_subpart_suppression():
    """Verify tracker separates adjacent vessels while suppressing internal sub-parts."""
    tracker = VesselTracker()

    # Two distinct adjacent vessels side by side at a pier
    ship_a = {"cx": 100.0, "cy": 100.0, "w": 30.0, "h": 80.0, "confidence": 0.92,
              "bbox": [85.0, 60.0, 115.0, 140.0]}
    ship_b = {"cx": 145.0, "cy": 100.0, "w": 30.0, "h": 80.0, "confidence": 0.90,
              "bbox": [130.0, 60.0, 160.0, 140.0]}

    t1 = tracker.update([ship_a, ship_b])
    assert len(t1) == 2, "Adjacent vessels must receive separate tracks"
    assert t1[0]["track_id"] != t1[1]["track_id"]

    # In next frame, an erroneous sub-part detection inside Ship A appears along with Ship A & B
    deck_sliver = {"cx": 102.0, "cy": 105.0, "w": 10.0, "h": 15.0, "confidence": 0.85,
                   "bbox": [97.0, 97.5, 107.0, 112.5]}
    t2 = tracker.update([ship_a, ship_b, deck_sliver])
    # The deck sliver inside Ship A must be suppressed from creating a 3rd distinct track
    assert len(t2) == 2, f"Subpart should be suppressed, got {len(t2)} tracks"


def test_ppo_scheduler_actions_and_safety_override():
    """Verify PPO policy action selection and safety override layer."""
    sched = AdaptiveComputeScheduler("models/weights/ppo_scheduler.zip")

    # 1. Quiescent / Empty Sea: Target not visible, 0 tracks, low motion
    obs_empty = sched.build_observation(
        target_visible=False,
        detection_count=0,
        active_track_count=0,
        avg_confidence=0.0,
        motion_level=0.0,
    )
    action_empty, mode_empty, override_empty = sched.select_action(obs_empty)
    assert mode_empty == "lightweight"
    assert action_empty == 0
    assert override_empty is False

    # 2. Multi-vessel / dense tracking: multiple active tracks in scene
    obs_multi = sched.build_observation(
        target_visible=True,
        detection_count=3,
        active_track_count=3,
        avg_confidence=0.90,
    )
    action_multi, mode_multi, override_multi = sched.select_action(obs_multi)
    assert action_multi == 2
    assert mode_multi == "heavy"


def test_backend_api_endpoints():
    """Verify FastAPI backend endpoints."""
    client = TestClient(app)

    # Health endpoint
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    # Satellite detect endpoint
    sample_img = Path("data/vhrv/vhrv/images/test/vhrv_00050.jpg")
    if sample_img.exists():
        with open(sample_img, "rb") as f:
            r_sat = client.post("/satellite/detect", files={"file": ("test.jpg", f, "image/jpeg")})
        assert r_sat.status_code == 200
        res = r_sat.json()
        assert res["status"] == "success"
        assert res["ship_count"] >= 1
        assert "annotated_image_url" in res
