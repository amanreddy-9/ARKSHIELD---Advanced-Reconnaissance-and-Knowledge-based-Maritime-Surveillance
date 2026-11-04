"""Capture unchanged detections and baseline tracking for fair repair comparisons."""
from pathlib import Path
import json,time,hashlib,sys
import cv2,torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models.detector import VesselDetector
from rl.scheduler import AdaptiveComputeScheduler
OUT=Path((ROOT/'outputs/diagnostics/tracking_repair_latest.txt').read_text().strip())
sys.path.insert(0,str(OUT/'source_backup'))
from tracking.kalman_tracker import KalmanTracker
from tracking.association import bbox_iou
class BaselineFiltering:
 def _filter_detections(self,detections,confidence_threshold=.18,iou_threshold=.50):
  filtered=[]
  for d in sorted(detections,key=lambda x:x.get('confidence',0),reverse=True):
   if d.get('confidence',0)>=confidence_threshold and d.get('bbox') and not any(bbox_iou(d['bbox'],a['bbox'])>iou_threshold for a in filtered):filtered.append(d)
  return filtered
detector=VesselDetector();filtering=BaselineFiltering()
print('CUDA',torch.cuda.is_available(),flush=True)
inputs=json.loads((OUT/'input_inventory.json').read_text())
for item in inputs:
 p=Path(item['path']);sample=2 if p.name=='test1.mp4' else 1
 c=cv2.VideoCapture(str(p));frames=[];t0=time.perf_counter();idx=0
 while True:
  ok,frame=c.read()
  if not ok:break
  if idx%sample==0:
   ds=filtering._filter_detections(detector.predict(frame,mode='drone',conf=.18,iou=.45),confidence_threshold=.18,iou_threshold=.50)
   frames.append({'frame_index':idx,'timestamp':idx/item['fps'],'detections':ds})
   if len(frames)%120==0:print(p.name,'detected frames',len(frames),flush=True)
  idx+=1
 c.release();elapsed=time.perf_counter()-t0
 cache={'input':item,'sample_every':sample,'detector_settings':{'conf':.18,'iou':.45,'filter_iou':.50,'imgsz':640},'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'detection_seconds':elapsed,'frames':frames}
 (OUT/(p.stem+'_detections.json')).write_text(json.dumps(cache))
 for mode in ['full','ppo']:
  tracker=KalmanTracker();scheduler=AdaptiveComputeScheduler();rows=[];counts=[];last_dets=[];calls=0;deletions=[];t0=time.perf_counter()
  for j,fr in enumerate(frames):
   obs=scheduler.build_observation(target_visible=bool(counts and counts[-1]),detection_count=counts[-1] if counts else 0,active_track_count=sum(t.missed<=3 and t.state=='confirmed' for t in tracker.tracks.values()),avg_confidence=sum(d['confidence'] for d in last_dets)/len(last_dets) if last_dets else 0,frame_progress=fr['frame_index']/item['frames'])
   action,_,_=scheduler.select_action(obs) if mode=='ppo' else (2,'heavy',False)
   ran=action==2 or (j+1)%(2 if action==1 else 4)==0;ds=fr['detections'] if ran else [];calls+=int(ran)
   if ran:last_dets=ds
   counts.append(len(ds));old=set(tracker.tracks);tracks=tracker.update(ds);deleted=sorted(old-set(tracker.tracks));deletions.extend(deleted)
   rows.append({'frame_index':fr['frame_index'],'timestamp':fr['timestamp'],'tracks':tracks,'all_tracks':tracker.last_diagnostics['tracks'],'deleted':deleted,'inference_ran':ran,'ppo_action':action})
  summary={'unique_ids':tracker.next_id-1,'deletions':len(deletions),'matched_observations':sum(len(x['tracks']) for x in rows),'detector_calls':calls,'detector_call_reduction_pct':100*(1-calls/len(rows)),'tracking_seconds':time.perf_counter()-t0,'ground_truth_identity_metrics':'unavailable'}
  (OUT/(p.stem+'_baseline_'+mode+'.json')).write_text(json.dumps({'summary':summary,'frames':rows}))
  print(p.name,mode,summary,flush=True)
print('BASELINE_COMPLETE',str(OUT),flush=True)
