"""Replay unchanged cached YOLO detections; identity metrics require ground truth."""
from pathlib import Path
import sys,json,time,collections,datetime,hashlib
import cv2,numpy as np,imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tracking.kalman_tracker import KalmanTracker
from tracking.camera_motion import CameraMotionEstimator
from tracking.telemetry import TrackingDiagnosticCSV,draw_tracking
from rl.scheduler import AdaptiveComputeScheduler
OUT=Path((ROOT/'outputs/diagnostics/tracking_repair_latest.txt').read_text().strip())
CACHE_DIR=OUT
OUT=OUT/('benchmark_final_'+datetime.datetime.now().strftime('%H%M%S'));OUT.mkdir(exist_ok=False)
(CACHE_DIR/'final_benchmark_path.txt').write_text(str(OUT))
(OUT/'implementation_sha256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tracking').glob('*.py')},indent=2))
comparison=[]
for cache_path in CACHE_DIR.glob('*_detections.json'):
 cache=json.loads(cache_path.read_text());name=cache.get('case_name',Path(cache['input']['path']).stem)
 for mode in ['full','ppo']:
  tr=KalmanTracker();motion=CameraMotionEstimator();scheduler=AdaptiveComputeScheduler()
  cap=cv2.VideoCapture(cache['input']['path']);decoded_index=-1;rows=[];counts=[];last_dets=[];calls=0;motion_time=0.;tracking_time=0.;cuts=[]
  events=collections.Counter();video=None
  csvlog=TrackingDiagnosticCSV(OUT/f'{name}_repaired_{mode}.csv')
  for j,fr in enumerate(cache['frames']):
   while decoded_index<fr['frame_index']:
    ok,frame=cap.read();decoded_index+=1
    if not ok:break
   if not ok:raise RuntimeError(f'Cannot decode original frame {fr["frame_index"]}')
   start=time.perf_counter();cam=motion.update(frame,[t.bbox for t in tr.tracks.values()]);motion_time+=time.perf_counter()-start
   if cam['scene_cut']:scheduler.reset();counts=[];last_dets=[];cuts.append(fr['frame_index'])
   obs=scheduler.build_observation(target_visible=bool(counts and counts[-1]),detection_count=counts[-1] if counts else 0,
    active_track_count=sum(t.state=='confirmed' and t.missed<=3 for t in tr.tracks.values()),
    avg_confidence=sum(d['confidence'] for d in last_dets)/len(last_dets) if last_dets else 0,frame_progress=fr['frame_index']/cache['input']['frames'])
   action,processing,override=scheduler.select_action(obs) if mode=='ppo' else (2,'heavy',False)
   if j==0 or cam['scene_cut']:action,processing,override=2,'heavy',True
   elif any(t.state=='lost' for t in tr.tracks.values()) and action==0:action,processing,override=1,'standard',True
   ran=action==2 or (j+1)%(2 if action==1 else 4)==0
   ds=fr['detections'] if ran else [];calls+=int(ran)
   if ran:counts.append(len(ds));last_dets=ds
   motion.exclude_current_boxes([d['bbox'] for d in ds],frame.shape[1])
   start=time.perf_counter();tracks=tr.update(ds,timestamp=fr['timestamp'],inference_ran=ran,
    camera_transform=cam['affine'],scene_cut=cam['scene_cut'],include_predictions=True,camera_status=cam['status']);tracking_time+=time.perf_counter()-start
   diag=tr.last_diagnostics;events.update(e['event'] for e in diag['events']);csvlog.write(fr['frame_index'],fr['timestamp'],diag,action)
   rows.append({'frame_index':fr['frame_index'],'timestamp':fr['timestamp'],'tracks':tracks,'diagnostics':diag,'camera':{k:v for k,v in cam.items() if k!='affine'},'inference_ran':ran,'ppo_action':action})
   if video is None:
    video=imageio_ffmpeg.write_frames(str(OUT/f'{name}_repaired_{mode}.mp4'),(frame.shape[1],frame.shape[0]),fps=cache['input']['fps']/cache['sample_every'],codec='libx264',pix_fmt_in='bgr24',pix_fmt_out='yuv420p',ffmpeg_log_level='error');video.send(None)
   video.send(draw_tracking(frame,tracks,diag,fr['frame_index'],processing,override))
   if (j+1)%120==0:print(name,mode,j+1,'frames',flush=True)
  cap.release();csvlog.close();video.close()
  summary={'unique_ids':tr.next_id-1,'deletions':events['deleted'],'recoveries':events['recovered'],'scene_cut_frames':cuts,
   'matched_observations':sum(sum(t['observed'] for t in row['tracks']) for row in rows),'detector_calls':calls,
   'detector_call_reduction_pct':100*(1-calls/len(rows)),'tracking_seconds':tracking_time,'tracking_fps':len(rows)/max(tracking_time,1e-8),
   'camera_seconds':motion_time,'camera_ms_per_frame':1000*motion_time/len(rows),
   'estimated_fullrate_detection_fps':len(rows)/cache['detection_seconds'],
   'identity_metrics':{'ID_switches':None,'fragmentation':None,'IDF1':None,'HOTA':None,'false_associations':None,'reason':'No ground-truth identities provided; unique IDs are not ID switches across cuts.'}}
  (OUT/f'{name}_repaired_{mode}.json').write_text(json.dumps({'summary':summary,'frames':rows}))
  before=json.loads((CACHE_DIR/f'{name}_baseline_{mode}.json').read_text())['summary']
  comparison.append({'video':name,'mode':mode,'before':before,'after':summary})
  (OUT/'comparison.json').write_text(json.dumps(comparison,indent=2))
  print(name,mode,'BEFORE',before['unique_ids'],'AFTER',summary,flush=True)
print('BENCHMARK_COMPLETE',flush=True)
