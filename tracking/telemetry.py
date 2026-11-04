"""Shared honest video rendering and append-only CSV diagnostics."""
import csv,json
from pathlib import Path
import cv2


class TrackingDiagnosticCSV:
    fields=['frame','timestamp','track_id','track_state','predicted_bbox','observed_bbox','velocity','uncertainty','matching_cost','matching_stage','detection_confidence','ppo_action','inference_ran','seconds_since_detection','event','reason','scene_cut','camera_status']
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('x',newline='',encoding='utf-8');self.writer=csv.DictWriter(self.file,fieldnames=self.fields);self.writer.writeheader()
    def write(self,frame,timestamp,diagnostics,ppo_action):
        events=diagnostics.get('events',[])
        rows=diagnostics.get('tracks',[])+diagnostics.get('deleted_tracks',[])
        for tr in rows:
            relevant=[e for e in events if e.get('track_id')==tr['track_id']]
            if not relevant: relevant=[{'event':tr.get('status','tracked'),'reason':''}]
            for event in relevant:
                d=tr.get('matched_detection') or {}
                self.writer.writerow({'frame':frame,'timestamp':timestamp,'track_id':tr['track_id'],
                    'track_state':tr.get('lifecycle_state',tr['state']),'predicted_bbox':json.dumps(tr.get('predicted_bbox')),
                    'observed_bbox':json.dumps(d.get('bbox')),'velocity':json.dumps([tr['vx'],tr['vy']]),
                    'uncertainty':json.dumps(tr.get('covariance_diagonal')),'matching_cost':tr.get('matching_cost'),
                    'matching_stage':tr.get('matching_stage'),'detection_confidence':d.get('confidence'),
                    'ppo_action':ppo_action,'inference_ran':diagnostics.get('inference_ran'),
                    'seconds_since_detection':tr.get('seconds_since_measurement'),'event':event.get('event'),
                    'reason':event.get('reason',''),'scene_cut':diagnostics.get('scene_cut'),
                    'camera_status':diagnostics.get('camera_status')})
        if diagnostics.get('scene_cut'):
            self.writer.writerow({'frame':frame,'timestamp':timestamp,'event':'scene_cut','reason':'tracking_restarted','scene_cut':True,'camera_status':diagnostics.get('camera_status')})
        self.file.flush()
    def close(self):self.file.close()


def draw_tracking(frame,tracks,diagnostics,frame_index,mode,override=False):
    out=frame.copy();h,w=out.shape[:2]
    for tr in tracks:
        observed=tr.get('observed',True);box=tr.get('detection_bbox') or tr.get('bbox')
        if box is None:box=[tr['cx']-tr['w']/2,tr['cy']-tr['h']/2,tr['cx']+tr['w']/2,tr['cy']+tr['h']/2]
        x1,y1,x2,y2=map(int,box)
        if x2<0 or y2<0 or x1>=w or y1>=h:continue
        x1=max(0,x1);y1=max(0,y1);x2=min(w-1,x2);y2=min(h-1,y2)
        if x2<=x1 or y2<=y1:continue
        color=(100,220,100) if observed else (50,190,240)
        if observed:cv2.rectangle(out,(x1,y1),(x2,y2),color,2)
        else:
            for x in range(x1,x2,16):
                cv2.line(out,(x,y1),(min(x+8,x2),y1),color,2);cv2.line(out,(x,y2),(min(x+8,x2),y2),color,2)
            for y in range(y1,y2,16):
                cv2.line(out,(x1,y),(x1,min(y+8,y2)),color,2);cv2.line(out,(x2,y),(x2,min(y+8,y2)),color,2)
        stable=tr.get('classification_stable') or {};raw=tr.get('classification') or {}
        label=stable.get('display_label') or stable.get('label') or raw.get('label') or 'Vessel'
        evidence=f" | score share {stable['stability']:.0%}" if stable.get('observations',0)>=2 else ''
        status=tr.get('status','DETECTED' if observed else 'PREDICTED')
        text=f"ID {tr['track_id']:02d} | {status} | {label}{evidence}"
        (tw,th),_=cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,.48,1)
        tx=min(x1,max(0,w-tw-8));ty=max(th+5,y1-5)
        cv2.rectangle(out,(tx,ty-th-4),(min(w-1,tx+tw+6),ty+4),(18,24,38),-1)
        cv2.putText(out,text,(tx+3,ty),cv2.FONT_HERSHEY_SIMPLEX,.48,(230,210,90),1,cv2.LINE_AA)
    observed=diagnostics.get('detected_vessels',sum(t.get('observed',True) for t in tracks))
    text=f"Frame {frame_index} | Detected: {observed} | Confirmed: {diagnostics.get('confirmed_tracks',0)} | Coasting: {diagnostics.get('coasting_tracks',0)} | Recovered: {diagnostics.get('recovered_tracks',0)} | Deleted: {len(diagnostics.get('deleted_tracks',[]))} | PPO: {mode}"
    cv2.rectangle(out,(5,5),(w-5,35),(14,20,32),-1)
    cv2.putText(out,text,(10,26),cv2.FONT_HERSHEY_SIMPLEX,.42,(170,230,220),1,cv2.LINE_AA)
    if diagnostics.get('scene_cut'):
        cv2.putText(out,'Scene changed - tracking restarted',(10,57),cv2.FONT_HERSHEY_SIMPLEX,.55,(80,190,255),1,cv2.LINE_AA)
    if override:cv2.putText(out,'Safety override',(w-150,55),cv2.FONT_HERSHEY_SIMPLEX,.45,(80,190,255),1)
    return out
