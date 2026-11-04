"""Exercise the real pipeline without external VLM calls or rewriting analytics."""
from pathlib import Path
import sys,json,time,hashlib,datetime,cv2
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pipeline.orchestrator import OATrackPipeline
OUT=Path((ROOT/'outputs/diagnostics/tracking_repair_latest.txt').read_text().strip())/('application_final_'+datetime.datetime.now().strftime('%H%M%S'));OUT.mkdir(exist_ok=False)
weights=list((ROOT/'models/weights').rglob('*.pt'))+list((ROOT/'models/weights').rglob('*.zip'))+[ROOT/'yolo11n.pt']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in weights}
(OUT.parent/'final_application_path.txt').write_text(str(OUT))
pipeline=OATrackPipeline();results=[]
for name,sample in [('Destroyer1.mp4',1),('DestroFri.mp4',2),('test1.mp4',2)]:
 start=time.perf_counter();result=pipeline.drone_video(str(ROOT/'data/test_mp4'/name),sample_every=sample,
    use_ppo=True,output_dir=OUT,write_analytics=False,vlm_enabled=False)
 elapsed=time.perf_counter()-start
 assert result['status']=='success';errors=[f for f in result['frames'] if f.get('processing_mode')=='error'];assert not errors,errors[:2]
 output=Path(result['annotated_video_path']);cap=cv2.VideoCapture(str(output));count=0
 while True:
  ok,frame=cap.read()
  if not ok:break
  count+=1
 cap.release();assert count==result['processed_frames'],(count,result['processed_frames'])
 assert Path(result['tracking_diagnostic_csv']).exists()
 json.dumps(result,allow_nan=False)
 summary={'video':name,'sample_every':sample,'unique_ids':result['unique_track_count'],'frames':count,
  'pipeline_seconds':elapsed,'pipeline_fps':count/elapsed,'detector_calls':result['yolo_calls'],
  'detector_call_reduction_pct':result['detector_call_reduction_pct'],'scene_cuts':sum(f.get('scene_cut',False) for f in result['frames']),
  'coasting_frames':sum(f.get('coasting_track_count',0)>0 for f in result['frames']),
  'recovery_events':sum(f.get('recovered_track_count',0) for f in result['frames']),
  'classifier_calls':result['classifier_calls'],'vlm_calls':'disabled for reproducible offline evaluation',
  'output_video':str(output),'diagnostic_csv':result['tracking_diagnostic_csv']}
 (OUT/(Path(name).stem+'_response.json')).write_text(json.dumps(result))
 results.append(summary);(OUT/'integration_results.json').write_text(json.dumps(results,indent=2));print(summary,flush=True)
assert hashes=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in weights}
(OUT/'weights_preservation.json').write_text(json.dumps({'unchanged':True,'sha256':hashes},indent=2))
from fastapi.testclient import TestClient
from backend.main import app
with TestClient(app) as client:
 for endpoint in ['/health','/drone/presets','/satellite/presets']:
  response=client.get(endpoint);assert response.status_code==200,(endpoint,response.status_code)
print('PIPELINE_AND_API_VERIFIED',flush=True)
