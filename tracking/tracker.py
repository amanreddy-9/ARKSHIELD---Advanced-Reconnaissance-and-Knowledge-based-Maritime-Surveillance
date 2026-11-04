"""
tracking/tracker.py
Modular Tracking Facade for OATrack-VLM.

Provides backwards compatibility with the existing codebase:
- Re-exports KalmanTracker as VesselTracker
- Re-exports Track, bbox_iou, size_similarity
- Seamless integration with pipeline/orchestrator.py, tests, and API
"""
from tracking.base_tracker import BaseTracker
from tracking.kalman_filter import KalmanFilter
from tracking.track import Track
from tracking.association import bbox_iou, size_similarity, compute_association_cost, is_subpart_detection
from tracking.kalman_tracker import KalmanTracker

# Backwards compatibility alias: VesselTracker is now powered by KalmanTracker
VesselTracker = KalmanTracker

__all__ = [
    "BaseTracker",
    "KalmanFilter",
    "Track",
    "KalmanTracker",
    "VesselTracker",
    "bbox_iou",
    "size_similarity",
    "compute_association_cost",
    "is_subpart_detection",
]
