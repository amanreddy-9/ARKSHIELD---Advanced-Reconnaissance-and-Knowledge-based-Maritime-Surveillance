from rl.scheduler import AdaptiveComputeScheduler
from tracking.tracker import VesselTracker

def test_scheduler():
    s=AdaptiveComputeScheduler()
    assert s.select_mode(False,0.0)=="lightweight"
    assert s.select_mode(True,0.9)=="heavy"

def test_tracker():
    t=VesselTracker()
    assert t.update([{"cx":10,"cy":10}])[0]["track_id"]==1
