import json
from pathlib import Path
import pytest
from tracking.tracker import VesselTracker, bbox_iou, size_similarity


def test_bbox_iou_calculation():
    box1 = [10.0, 10.0, 50.0, 50.0]
    box2 = [10.0, 10.0, 50.0, 50.0]
    assert bbox_iou(box1, box2) == 1.0

    box3 = [100.0, 100.0, 150.0, 150.0]
    assert bbox_iou(box1, box3) == 0.0

    box4 = [30.0, 10.0, 70.0, 50.0]
    iou = bbox_iou(box1, box4)
    assert 0.30 <= iou <= 0.40


def test_size_similarity():
    assert size_similarity(50.0, 50.0, 50.0, 50.0) == 1.0
    sim = size_similarity(50.0, 50.0, 10.0, 10.0)
    assert sim < 0.50


def test_tracker_continuity_on_moving_vessel():
    tracker = VesselTracker()
    # Vessel moves across 5 frames with 10px step
    for i in range(5):
        det = {
            "cx": 100.0 + i * 10.0,
            "cy": 100.0 + i * 5.0,
            "w": 60.0,
            "h": 30.0,
            "confidence": 0.90,
            "bbox": [70.0 + i * 10.0, 85.0 + i * 5.0, 130.0 + i * 10.0, 115.0 + i * 5.0]
        }
        tracks = tracker.update([det])
        assert len(tracks) == 1
        assert tracks[0]["track_id"] == 1


def test_tracker_continuity_with_dropped_frame():
    tracker = VesselTracker()
    # Frame 1: Vessel detected
    det1 = {"cx": 100.0, "cy": 100.0, "w": 60.0, "h": 30.0, "confidence": 0.90}
    t1 = tracker.update([det1])
    assert t1[0]["track_id"] == 1

    # Frame 2: Vessel not detected (dropped/occluded)
    t2 = tracker.update([])
    assert len(t2) == 0

    # Frame 3: Vessel reappears nearby
    det3 = {"cx": 115.0, "cy": 105.0, "w": 60.0, "h": 30.0, "confidence": 0.88}
    t3 = tracker.update([det3])
    assert len(t3) == 1
    # MUST retain the same track ID 1
    assert t3[0]["track_id"] == 1


def test_real_drone_oil_tanker_continuity():
    json_path = Path("data/test_mp4/Oil tanker with a drone! #shorts #merchantnavy #ships #viral #trending #dronevideo #drone #oiltanker_result.json")
    if not json_path.exists():
        pytest.skip("Test video JSON result not found")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    tracker = VesselTracker()
    all_tracks = set()

    for frame in data["frames"]:
        tracks = tracker.update(frame["detections"])
        for tr in tracks:
            all_tracks.add(tr["track_id"])

    # Original tracker produced 27 fragmented tracks.
    # Improved tracker with IoU matching and recovery must produce <= 20 total tracks
    # and confirmed persistent tracks (>= 3 hits) must be <= 15.
    print(f"Total unique tracks on oil tanker video: {len(all_tracks)}")
    assert len(all_tracks) <= 20

    # Verify that the primary track maintains substantial continuous coverage
    track_hits = {}
    tracker2 = VesselTracker()
    for frame in data["frames"]:
        for tr in tracker2.update(frame["detections"]):
            track_hits[tr["track_id"]] = track_hits.get(tr["track_id"], 0) + 1
    confirmed_tracks = [t for t, h in track_hits.items() if h >= 3]
    assert len(confirmed_tracks) <= 15
    assert max(track_hits.values()) >= 50
