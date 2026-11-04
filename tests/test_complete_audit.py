"""Audit regressions: detector geometry, lifecycle, color, evidence, registry."""
from collections import defaultdict, Counter
from types import SimpleNamespace as NS
from unittest.mock import Mock
import numpy as np
import pytest
import torch
from PIL import Image
from tracking.kalman_tracker import KalmanTracker
from models.detector import VesselDetector
from models.classifier import ShipClassifier
from pipeline.orchestrator import OATrackPipeline
from pipeline.track_registry import build_track_registry

def d(x=100,y=100,w=100,h=100):
 return dict(bbox=[x-w/2,y-h/2,x+w/2,y+h/2],cx=x,cy=y,w=w,h=h,confidence=.9)

def detector_with(boxes):
 detector=VesselDetector.__new__(VesselDetector);detector.drone_conf=.18;detector.drone_iou=.45
 detector.drone_model=Mock();detector.satellite_model=None
 detector.drone_model.predict.return_value=[NS(boxes=[NS(conf=torch.tensor(.9),xyxy=torch.tensor([b],dtype=torch.float)) for b in boxes])]
 return detector

def test_actual_detector_preserves_adjacent_center_inside_vessels():
 result=detector_with([[0,0,100,100],[40,0,140,100]])._predict_drone(np.zeros((200,200,3),np.uint8))
 assert len(result)==2 and result[0]['bbox']==[0,0,100,100]

def test_detector_containment_60_percent_without_parent_expansion():
 result=detector_with([[0,0,100,100],[70,20,110,60]])._predict_drone(np.zeros((200,200,3),np.uint8))
 assert len(result)==1 and result[0]['bbox']==[0,0,100,100]

def test_unmodified_satellite_confidence():
 detector=VesselDetector.__new__(VesselDetector);detector.is_custom=True;detector.conf=.25;detector.iou=.6
 detector.satellite_model=Mock();detector.model=None
 detector.satellite_model.predict.return_value=[NS(names={0:'vessel'},boxes=[NS(cls=torch.tensor(0),conf=torch.tensor(.5),xyxy=torch.tensor([[0,0,100,100]]))])]
 assert detector._predict_satellite('unused')[0]['confidence']==.5

def test_birth_plus_two_associations_confirmation_and_skips():
 t=KalmanTracker(confirm_hits=3)
 assert t.update([d()],timestamp=0)[0]['lifecycle_state']=='tentative'
 assert t.update([d()],timestamp=.1)[0]['lifecycle_state']=='tentative'
 t.update([],timestamp=.2,inference_ran=False)
 out=t.update([d()],timestamp=.3)
 assert out[0]['confirmed_identity'] and out[0]['hits']==3
 assert t.tracks[1].total_detector_misses==0
 coast=t.update([],timestamp=.4,include_predictions=True)
 assert coast[0]['lifecycle_state']=='coasting'
 assert t.update([d()],timestamp=.8)[0]['recovered']

def test_detector_miss_breaks_tentative_confirmation_streak():
 t=KalmanTracker(confirm_hits=3);t.update([d()],timestamp=0);t.update([],timestamp=.1)
 assert t.update([d()],timestamp=.2)[0]['lifecycle_state']=='tentative'
 assert t.update([d()],timestamp=.3)[0]['lifecycle_state']=='tentative'
 assert t.update([d()],timestamp=.4)[0]['confirmed_identity']

def test_false_positive_remains_tentative_then_deleted():
 t=KalmanTracker(confirm_hits=3);t.update([d()],timestamp=0)
 t.update([],timestamp=.8,include_predictions=True)
 assert not t.tracks
 assert t.last_diagnostics['deleted_tracks'][0]['reason']=='tentative_expired'
 assert not t.last_diagnostics['deleted_tracks'][0]['confirmed_identity']

def test_rgb_crop_and_invalid_offscreen_boxes():
 detector=VesselDetector.__new__(VesselDetector)
 bgr=np.zeros((100,100,3),np.uint8);bgr[:,:,2]=255
 crop=detector.crop(bgr,[10,10,60,60]);assert crop.getpixel((0,0))==(255,0,0)
 assert crop.size==(55,55)
 for box in [[50,50,10,10],[101,10,120,20],[0,0,float('nan'),10]]:
  with pytest.raises(ValueError):detector.crop(bgr,box)

def test_classifier_bgr_array_matches_rgb_pil_preprocessing():
 from torchvision import transforms
 c=ShipClassifier.__new__(ShipClassifier);c.device='cpu';c.CLASS_NAMES=ShipClassifier.CLASS_NAMES
 c.transform=transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
 c.model=Mock(return_value=torch.zeros((1,10)))
 bgr=np.zeros((50,100,3),np.uint8);bgr[:,:,2]=255
 c.classify(bgr,use_vlm_disambiguation=False);array_input=c.model.call_args.args[0].clone()
 c.classify(Image.fromarray(bgr[:,:,::-1]),use_vlm_disambiguation=False)
 assert torch.equal(array_input,c.model.call_args.args[0])

def history_pipeline():
 p=OATrackPipeline.__new__(OATrackPipeline);p.track_class_scores=defaultdict(lambda:defaultdict(float));p.track_class_counts=defaultdict(Counter);p.track_last_seen={};return p

def test_detector_confidence_weights_normalized_class_vectors():
 p=history_pipeline()
 p._update_track_classification(1,dict(label='Frigate',confidence=.8,detector_confidence=.9,probabilities={'Frigate':8,'Destroyer':2}),0)
 r=p._update_track_classification(1,dict(label='Destroyer',confidence=.9,detector_confidence=.1,probabilities={'Frigate':1,'Destroyer':9}),1)
 assert r['label']=='Frigate' and r['stability']==pytest.approx(.73)
 assert sum(p.track_class_scores[1].values())==pytest.approx(1.)
 # A real change can affect the estimate; no permanent class lock.
 for i in range(30):p._update_track_classification(1,dict(label='Destroyer',confidence=.9,detector_confidence=.9,probabilities={'Frigate':.1,'Destroyer':.9}),i+2)
 assert p._stable_track_classification(1)['label']=='Destroyer'
 assert p._stable_track_classification(2) is None

def test_registry_includes_unclassified_deleted_and_current_states():
 t=KalmanTracker(confirm_hits=3);frames=[]
 for i,ds in enumerate([[d()],[d()],[d()],[],[d(350)],[]]):
  timestamp=[0,.1,.2,.3,.4,1.2][i]
  t.update(ds,timestamp=timestamp,include_predictions=True)
  frames.append(dict(frame_index=i,tracking_diagnostics=t.last_diagnostics))
 rows,counts=build_track_registry(frames,{})
 assert rows['1']['lifecycle_state']=='coasting' and rows['1']['confirmed_identity']
 assert rows['2']['lifecycle_state']=='deleted' and rows['2']['observations']==0
 assert counts['coasting']==1 and counts['deleted_history']==1 and counts['all_time_tracks']==2
 assert rows['2']['deletion_reason']=='tentative_expired'


def test_high_confidence_truncated_hull_is_not_full_size_measurement():
 t=KalmanTracker(confirm_hits=3)
 for i in range(30):t.update([d(200,200,100,150)],timestamp=i/30)
 for i in range(30,60):t.update([d(200,220,100,100)],timestamp=i/30)
 assert t.tracks[1].measurement_components==[0,2]
 assert abs(t.tracks[1].vy)<1 and abs(t.tracks[1].h-150)<2
 assert len(t.tracks)==1


def test_classification_history_cannot_override_deleted_lifecycle():
 t=KalmanTracker(confirm_hits=3);frames=[]
 for i in range(3):
  t.update([d()],timestamp=i*.1);frames.append(dict(frame_index=i,tracking_diagnostics=t.last_diagnostics))
 t.update([],timestamp=7);frames.append(dict(frame_index=3,tracking_diagnostics=t.last_diagnostics))
 rows,counts=build_track_registry(frames,{'1':dict(label='Frigate',observations=3,lifecycle_state='confirmed',tracking_state='confirmed')})
 assert rows['1']['lifecycle_state']=='deleted' and not rows['1']['is_current']
 assert counts['deleted_history']==1

def test_motion_affinity_uses_velocity_in_correct_time_units():
 from tracking.track import Track
 from tracking.association import compute_association_cost
 timed=Track(1,d(w=100,h=50),time_aware=True)
 legacy=Track(1,d(w=100,h=50),time_aware=False)
 timed.dt=.1;legacy.dt=1.
 timed.kf.x[4,0]=100;timed.kf.x[5,0]=20
 legacy.kf.x[4,0]=10;legacy.kf.x[5,0]=2
 proposal=d(170,170,w=100,h=50)
 a=compute_association_cost(proposal,timed);b=compute_association_cost(proposal,legacy)
 assert a is not None and a==pytest.approx(b)
