"""Regression coverage for timing, occlusion, conservative matching and camera handling."""
import numpy as np
import cv2
import pytest
from collections import defaultdict,Counter
from tracking.kalman_filter import KalmanFilter
from tracking.kalman_tracker import KalmanTracker
from tracking.track import Track
from tracking.camera_motion import CameraMotionEstimator
from tracking.association import is_subpart_detection
from tracking.telemetry import draw_tracking


def det(x=100,y=100,w=60,h=30,conf=.9):
    return {'cx':x,'cy':y,'w':w,'h':h,'bbox':[x-w/2,y-h/2,x+w/2,y+h/2],'confidence':conf}


def test_dt_and_covariance_semigroup():
    a=KalmanFilter();a.initialize([100,100,60,30]);a.x[4:,0]=[20,-5,2,-1]
    b=KalmanFilter();b.initialize([100,100,60,30]);b.x=a.x.copy();b.P=a.P.copy()
    a.predict(.6);b.predict(.2);b.predict(.4)
    assert np.allclose(a.x,b.x);assert np.allclose(a.P,b.P)
    assert np.allclose(a.centroid,[112,97])
    a.update([111,98,61,30]);assert np.allclose(a.P,a.P.T)
    assert np.linalg.eigvalsh(a.P).min()>-1e-9


def test_covariance_growth_and_valid_size():
    k=KalmanFilter();k.initialize([0,0,2,2]);k.x[6:,0]=-20
    p=k.P.copy();k.predict(1)
    assert k.size==(1.,1.)
    k.predict(.5);assert np.linalg.eigvalsh(k.P).min()>-1e-8
    assert k.P[0,0]>p[0,0]


@pytest.mark.parametrize('fps,sample',[(15,1),(30,1),(60,2)])
def test_four_second_cloud_recovery_across_cadences(fps,sample):
    t=KalmanTracker();step=sample/fps
    for i in range(round(1/step)):
        ts=i*step;t.update([det(100+8*ts),det(300-4*ts,y=180)],timestamp=ts)
    initial=set(t.tracks)
    for i in range(round(1/step),round(5/step)):
        out=t.update([],timestamp=i*step,inference_ran=i%4==0,include_predictions=True)
        assert {x['track_id'] for x in out}==initial
        assert all(x['status']=='PREDICTED' for x in out)
    out=t.update([det(140),det(280,y=180)],timestamp=5.)
    assert {x['track_id'] for x in out}==initial
    assert all(x['recovered'] for x in out)
    assert t.last_diagnostics['stage_matches']==[0,0,2]


def test_skips_do_not_count_as_detector_misses():
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.05)
    before=t.tracks[1].inference_opportunities
    for i in range(1,11):t.update([],timestamp=.05+i*.05,inference_ran=False)
    tr=t.tracks[1];assert tr.detector_misses==0;assert tr.inference_opportunities==before
    assert tr.missed_frames==10;assert tr.seconds_since_measurement==pytest.approx(.5)
    t.update([],timestamp=.6,inference_ran=True);assert tr.detector_misses==1
    assert tr.kf.velocity==(0.,0.)


def test_expired_track_not_resurrected():
    t=KalmanTracker(max_unseen_seconds=1);t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    result=t.update([det()],timestamp=1.2)
    assert result[0]['track_id']==2
    assert any(e['reason']=='time_expired' for e in t.last_diagnostics['events'])


def test_uncertainty_expiry():
    t=KalmanTracker(max_position_std=30);t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    t.tracks[1].kf.P[0,0]=10000
    t.update([],timestamp=.2);assert not t.tracks
    assert t.last_diagnostics['deleted_tracks'][0]['reason']=='uncertainty_limit'


def test_far_and_wrong_shape_returns_rejected():
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    t.update([],timestamp=.5)
    out=t.update([det(1000),det(100,w=10,h=200)],timestamp=.6)
    assert 1 not in {tr['track_id'] for tr in out}
    assert t.tracks[1].observed is False


def test_similar_nearby_vessels_do_not_exchange_ids():
    t=KalmanTracker()
    for i in range(30):
        ts=i/30;t.update([det(100+20*ts,y=100),det(150-20*ts,y=145)],timestamp=ts)
    for i in range(30,60):t.update([],timestamp=i/30,inference_ran=i%3==0)
    out=t.update([det(110,y=145),det(140,y=100)],timestamp=2.)
    mapping={round(x['cy']):x['track_id'] for x in out}
    assert mapping[100]==1 and mapping[145]==2


def test_scene_cut_monotonic_ids_and_no_reassociation():
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    out=t.update([det()],timestamp=.2,scene_cut=True)
    assert out[0]['track_id']==2
    assert t.last_diagnostics['scene_cut']
    assert t.last_diagnostics['deleted_tracks'][0]['reason']=='scene_cut'
    assert t.last_diagnostics['deleted_tracks'][0]['lifecycle_state']=='deleted'


def test_timestamp_validation_and_one_prediction():
    t=KalmanTracker();t.update([det()],timestamp=0)
    t.update([],timestamp=.1,inference_ran=False);assert t.tracks[1].age==2
    with pytest.raises(ValueError):t.update([],timestamp=.1)
    with pytest.raises(ValueError):t.update([det()],timestamp=.2,inference_ran=False)


@pytest.mark.parametrize('angle,scale,translation',[(0,1,(8,5)),(5,1,(0,0)),(0,1.06,(0,0))])
def test_camera_background_translation_rotation_scale(angle,scale,translation):
    rng=np.random.default_rng(21)
    image=rng.integers(0,150,(300,400,3),dtype=np.uint8)
    image=cv2.GaussianBlur(image,(3,3),0)
    affine=cv2.getRotationMatrix2D((200,150),angle,scale);affine[:,2]+=translation
    current=cv2.warpAffine(image,affine,(400,300))
    motion=CameraMotionEstimator();motion.update(image)
    result=motion.update(current)
    assert not result['scene_cut'];assert result['affine'] is not None,result
    assert np.allclose(result['affine'],affine,atol=1.2)


def test_camera_insufficient_background_safe_fallback():
    m=CameraMotionEstimator();f=np.full((200,300,3),70,np.uint8);m.update(f)
    result=m.update(f);assert result['affine'] is None and not result['scene_cut']


def test_cloud_appearance_not_scene_cut():
    rng=np.random.default_rng(2);f=rng.integers(0,90,(240,320,3),dtype=np.uint8)
    m=CameraMotionEstimator();m.update(f)
    cloud=np.full_like(f,220);result=m.update(cloud)
    assert not result['scene_cut']


def test_abrupt_different_scene_cut():
    rng=np.random.default_rng(5)
    a=rng.integers(0,25,(240,320,3),dtype=np.uint8);a[:,:,0]+=170
    b=rng.integers(0,25,(240,320,3),dtype=np.uint8);b[:,:,1]+=210
    m=CameraMotionEstimator();m.update(a)
    assert m.update(b)['scene_cut']


def test_compensation_geometry_covariance_once():
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    m=np.array([[1.,0.,25],[0.,1.,10]])
    out=t.update([det(125,110)],timestamp=.2,camera_transform=m)
    assert out[0]['track_id']==1;assert abs(out[0]['cx']-125)<1
    assert t.tracks[1].vx==pytest.approx(250.,abs=1)
    assert np.linalg.eigvalsh(t.tracks[1].kf.P).min()>-1e-8


def test_subpart_suppression_does_not_remove_full_size_overlap():
    tr=Track(1,det(w=100,h=100))
    assert is_subpart_detection(det(w=20,h=20),[tr])
    assert not is_subpart_detection(det(135,w=100,h=100),[tr])


def test_prediction_rendering_distinct_and_clipped():
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    out=t.update([],timestamp=.2,inference_ran=False,include_predictions=True)
    image=draw_tracking(np.zeros((240,320,3),np.uint8),out,t.last_diagnostics,2,'standard')
    assert image.shape==(240,320,3)
    assert out[0]['matched_detection'] is None and out[0]['status']=='PREDICTED'
    assert tuple(image[85,70])==(50,190,240) # dashed amber rather than observed green


def test_classification_history_survives_recovery_without_fake_votes():
    from pipeline.orchestrator import OATrackPipeline
    p=OATrackPipeline.__new__(OATrackPipeline)
    p.track_class_scores=defaultdict(lambda:defaultdict(float));p.track_class_counts=defaultdict(Counter);p.track_last_seen={}
    p._update_track_classification(1,{'label':'Frigate','confidence':.8},0)
    t=KalmanTracker();t.update([det()],timestamp=0);t.update([det()],timestamp=.1)
    t.update([],timestamp=1);t.update([det()],timestamp=1.1)
    assert t.tracks[1].recovered
    stable=p._stable_track_classification(1);assert stable['observations']==1
    p._update_track_classification(1,{'label':'Frigate','confidence':.7},33)
    assert p._stable_track_classification(1)['observations']==2
    assert p._stable_track_classification(2) is None


def test_camera_velocity_survives_compensation_dropout_without_double_motion():
    t=KalmanTracker();t.update([det()],timestamp=0)
    m=np.array([[1.,0.,5],[0.,1.,0]])
    t.update([det(105)],timestamp=.1,camera_transform=m)
    t.update([det(110)],timestamp=.2,camera_transform=m)
    out=t.update([],timestamp=.3,inference_ran=False,include_predictions=True)
    assert out[0]['cx']==pytest.approx(115,abs=1)
    assert out[0]['vx']==pytest.approx(50,abs=1)


def test_merged_detection_does_not_spawn_or_corrupt_two_vessels():
    t=KalmanTracker();ds=[det(100,100,w=100,h=40),det(100,170,w=100,h=40)]
    t.update(ds,timestamp=0);t.update(ds,timestamp=.1)
    out=t.update([det(100,135,w=120,h=130)],timestamp=.2,include_predictions=True)
    assert {x['track_id'] for x in out}=={1,2}
    assert all(not x['observed'] for x in out)
    assert any(e.get('reason')=='merged_existing_vessels' for e in t.last_diagnostics['events'])
    out=t.update(ds,timestamp=.4);assert {x['track_id'] for x in out}=={1,2}


def test_full_size_adjacent_detection_not_suppressed_by_coasting_vessel():
    t=KalmanTracker();t.update([det(w=100,h=100)],timestamp=0);t.update([det(w=100,h=100)],timestamp=.1)
    t.update([],timestamp=.2)
    out=t.update([det(190,w=100,h=100)],timestamp=.3)
    assert out and out[0]['observed']


def test_low_brightness_discontinuity_still_detects_histogram_cut():
    rng=np.random.default_rng(9)
    a=rng.integers(0,5,(240,320,3),dtype=np.uint8);a[:,:,0]+=180
    b=rng.integers(0,5,(240,320,3),dtype=np.uint8);b[:,:,1]+=85
    m=CameraMotionEstimator();m.update(a)
    assert m.update(b)['scene_cut']


def test_partial_cloud_box_does_not_teach_false_vertical_motion():
    t=KalmanTracker()
    for i in range(30):t.update([det(200,200,w=120,h=100)],timestamp=i/30)
    for i in range(30,45):
        t.update([det(200,220,w=120,h=60,conf=.55)],timestamp=i/30)
    tr=t.tracks[1];assert tr.measurement_components==[0,2]
    assert abs(tr.vy)<1 and abs(tr.h-100)<2
    for i in range(45,120):t.update([],timestamp=i/30)
    out=t.update([det(200,200,w=120,h=100)],timestamp=4.)
    assert out[0]['track_id']==1
