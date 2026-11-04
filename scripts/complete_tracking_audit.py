"""Reproducible offline before/after audit; writes only to a new diagnostics run."""
import argparse,json,hashlib,time
from pathlib import Path
import cv2
from pipeline.orchestrator import OATrackPipeline

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True);parser.add_argument('--videos',nargs='+',default=['test2','test1','Destroyer1']);args=parser.parse_args()
 root=Path(Path('outputs/diagnostics/current_complete_audit.txt').read_text());folder=root/args.phase;folder.mkdir(exist_ok=False)
 p=OATrackPipeline();rows={}
 for name in args.videos:
  start=time.monotonic();r=p.drone_video('data/test_mp4/'+name+'.mp4',sample_every=2,output_dir=folder,write_analytics=False,vlm_enabled=False)
  (folder/(name+'_response.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
  tracks={}
  for f in r['frames']:
   diag=f.get('tracking_diagnostics',{})
   for tr in diag.get('tracks',[])+diag.get('deleted_tracks',[]):
    tid=str(tr['track_id']);row=tracks.setdefault(tid,dict(created_frame=f['frame_index'],initial_bbox=tr.get('bbox'),initial_confidence=tr['confidence'],events=[],observations=0))
    row.update(last_state=tr['lifecycle_state'],last_bbox=tr['bbox'])
    if tr.get('observed'):row['observations']+=1;row['last_observation']=f['frame_index']
    for e in diag.get('events',[]):
     if e.get('track_id')==tr['track_id']:row['events'].append(dict(frame=f['frame_index'],**e))
  summary=dict(processed_frames=r['processed_frames'],ids=r['unique_track_count'],classifier_calls=r['classifier_calls'],yolo_calls=r['yolo_calls'],error_frames=sum(f['processing_mode']=='error' for f in r['frames']),scene_cuts=sum(f.get('scene_cut',False) for f in r['frames']),recoveries=sum(f.get('recovered_track_count',0) for f in r['frames']),final_tracks=r['track_summaries'],track_state_counts=r.get('track_state_counts'),seconds=time.monotonic()-start,video=r['annotated_video_path'])
  rows[name]=summary
  (folder/(name+'_track_events.json')).write_text(json.dumps(tracks,indent=2))
  print(name,json.dumps(summary),flush=True)
 (folder/'summary.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
