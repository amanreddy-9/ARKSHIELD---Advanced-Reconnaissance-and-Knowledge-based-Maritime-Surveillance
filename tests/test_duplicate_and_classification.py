"""Duplicate births and honest fine-grained class presentation regressions."""
from collections import defaultdict,Counter
import numpy as np
from tracking.kalman_tracker import KalmanTracker

def det(x=200,y=200,w=100,h=100):
    return dict(bbox=[x-w/2,y-h/2,x+w/2,y+h/2],confidence=.9,cx=x,cy=y,w=w,h=h)

def test_near_identical_detector_boxes_create_one_track():
    t=KalmanTracker()
    result=t.update([det(),det(202,201)],timestamp=0)
    assert len(result)==1 and len(t.tracks)==1
    assert any(e.get('reason')=='duplicate_detector_proposal' for e in t.last_diagnostics['events'])

def test_statistically_rejected_overlapping_box_does_not_spawn_id():
    t=KalmanTracker()
    for i in range(20):t.update([det()],timestamp=i/30)
    # Abrupt full-box height change fails size innovation; do not turn it
    # into a new vessel on the same footprint.
    result=t.update([det(h=180)],timestamp=20/30,include_predictions=True)
    assert len(t.tracks)==1 and {r['track_id'] for r in result}=={1}
    assert any(e.get('reason')=='duplicate_track_birth_deferred' for e in t.last_diagnostics['events'])
    result=t.update([det()],timestamp=21/30)
    assert result[0]['track_id']==1

def test_two_overlapping_adjacent_vessels_stay_separate():
    t=KalmanTracker()
    for i in range(10):
        result=t.update([det(200+i),det(260+i)],timestamp=i/30,include_predictions=True)
        assert {r['track_id'] for r in result}=={1,2}
    result=t.update([],timestamp=.4,include_predictions=True)
    assert len(result)==2  # coasting does not globally suppress overlap

def test_close_frigate_destroyer_scores_remain_uncertain():
    from pipeline.orchestrator import OATrackPipeline
    p=OATrackPipeline.__new__(OATrackPipeline)
    p.track_class_scores=defaultdict(lambda:defaultdict(float))
    p.track_class_counts=defaultdict(Counter);p.track_last_seen={}
    for i in range(20):
        r=p._update_track_classification(1,dict(label='Destroyer',confidence=.51,
             probabilities={'Destroyer':.51,'Frigate':.49}),i)
    assert r['uncertain'] and r['display_label']=='Frigate / Destroyer (uncertain)'
    assert r['stability']==.51
    assert p._stable_track_classification(1)['observations']==20

def test_clear_prediction_is_estimate_not_verified_identity():
    from pipeline.orchestrator import OATrackPipeline
    p=OATrackPipeline.__new__(OATrackPipeline)
    p.track_class_scores=defaultdict(lambda:defaultdict(float))
    p.track_class_counts=defaultdict(Counter);p.track_last_seen={}
    for i in range(5):
        r=p._update_track_classification(1,dict(label='Frigate',confidence=.9,
             probabilities={'Frigate':.9,'Destroyer':.1}),i)
    assert not r['uncertain'] and r['display_label']=='Frigate (model estimate)'

