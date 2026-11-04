"""
tracking/base_tracker.py
Abstract Base Class for Maritime Vessel Trackers.
Provides a standard interface for swapping tracker backends:
(KalmanTracker, ByteTrack, DeepSORT, BoT-SORT, etc.)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTracker(ABC):
    """
    Abstract Base Class for Multi-Object Trackers in OATrack-VLM.
    All tracking implementations must inherit from this class.
    """

    def __init__(self, high_threshold: float = 0.40, low_threshold: float = 0.15, max_missed: int = 45):
        self.high_threshold = float(high_threshold)
        self.low_threshold = float(low_threshold)
        self.max_missed = int(max_missed)
        self.tracks: Dict[int, Any] = {}
        self.next_id: int = 1

    @abstractmethod
    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ingest current frame detections and return active, confirmed track dictionaries.

        Parameters:
            detections: List of detection dicts with 'bbox' ([x1,y1,x2,y2]) or ('cx','cy','w','h')
                        and 'confidence'.

        Returns:
            List of track dicts representing active vessels in current frame.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset all internal tracker state and ID counters."""
        self.tracks.clear()
        self.next_id = 1
