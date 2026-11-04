import sys
sys.path.insert(0, ".")
import json
from tracking.tracker import VesselTracker

with open("data/test_mp4/Oil tanker with a drone! #shorts #merchantnavy #ships #viral #trending #dronevideo #drone #oiltanker_result.json", encoding="utf-8") as f:
    data = json.load(f)

tracker = VesselTracker()
track_spans = {}

for frame_idx, frame in enumerate(data["frames"]):
    tracks = tracker.update(frame["detections"])
    for tr in tracks:
        tid = tr["track_id"]
        if tid not in track_spans:
            track_spans[tid] = [frame_idx, frame_idx, 1]
        else:
            track_spans[tid][1] = frame_idx
            track_spans[tid][2] += 1

print("=" * 60)
print(f"OATrack-VLM Tracker Benchmark on Oil Tanker Drone Video")
print(f"Total Frames: {len(data['frames'])}")
print(f"Unique Track IDs: {len(track_spans)} (Baseline was 27)")
print("=" * 60)
for tid, (start, end, obs) in sorted(track_spans.items(), key=lambda x: -x[1][2]):
    print(f"  Track ID {tid:2d}: frames {start:3d} to {end:3d} (span {end - start + 1:3d} frames, observations: {obs:2d})")
print("=" * 60)
