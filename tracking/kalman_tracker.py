"""Time-aware 8-state Kalman tracking with three-stage Hungarian association.
Timestamp-free update(detections) remains a frame-based compatibility API.
Timestamp-aware video tracking uses seconds and keeps confirmed coasting tracks.
"""
import math
import numpy as np
from tracking.base_tracker import BaseTracker
from tracking.track import Track
from tracking.association import associate_detections_to_tracks, compute_association_cost, is_subpart_detection, bbox_iou, same_vessel_footprint


class KalmanTracker(BaseTracker):
    def __init__(self, high_threshold=.40, low_threshold=.15, max_missed=45,
                 confirm_hits=2, max_unseen_seconds=6.0,
                 tentative_seconds=.75, max_position_std=400., recent_seconds=.25):
        super().__init__(high_threshold,low_threshold,max_missed)
        if confirm_hits<1 or max_unseen_seconds<=0 or tentative_seconds<=0 or max_position_std<=0:
            raise ValueError('Invalid track lifecycle configuration')
        self.confirm_hits=int(confirm_hits)
        self.max_unseen_seconds=float(max_unseen_seconds)
        self.tentative_seconds=float(tentative_seconds)
        self.max_position_std=float(max_position_std)
        self.recent_seconds=float(recent_seconds)
        self.last_diagnostics={}; self._timestamp=None; self._time_aware=False

    def reset(self):
        self.next_id=1; self.tracks.clear(); self.last_diagnostics={}
        self._timestamp=None; self._time_aware=False

    def create_track(self,detection):
        tid=self.next_id; self.next_id+=1
        self.tracks[tid]=Track(tid,detection,timestamp=self._timestamp or 0.,
                              time_aware=self._time_aware,confirm_hits=self.confirm_hits)
        return tid

    def update(self,detections,timestamp=None,inference_ran=True,
               camera_transform=None,scene_cut=False,include_predictions=False,
               camera_status='not_requested'):
        if not inference_ran and detections:
            raise ValueError('Skipped inference cannot supply current detections')
        timed=timestamp is not None
        now=float(timestamp) if timed else (self._timestamp or 0.)+1.
        if not math.isfinite(now) or (self._timestamp is not None and now<=self._timestamp):
            raise ValueError('Tracker timestamps must be finite and strictly increasing')
        if self._timestamp is not None and timed!=self._time_aware:
            raise ValueError('Reset tracker before changing timestamp units')
        dt=0. if self._timestamp is None else now-self._timestamp
        self._timestamp=now; self._time_aware=timed
        events=[]; deleted=[]; stage_counts=[0,0,0]; associations=[]

        def remove(tid,reason):
            tr=self.tracks[tid]; tr.tracking_state=Track.STATE_DELETED
            row=tr.to_dict(); row.update(event='deleted',reason=reason,lifecycle_state='deleted',status='DELETED')
            deleted.append(row); events.append({'event':'deleted','track_id':tid,'reason':reason})
            del self.tracks[tid]

        if scene_cut:
            for tid in list(self.tracks): remove(tid,'scene_cut')
            events.append({'event':'scene_cut','reason':'incompatible_camera_shot'})
        for tid,tr in list(self.tracks.items()):
            tr.predict(dt,now,inference_ran)
            if camera_transform is not None: tr.compensate_camera(camera_transform)
            if timed:
                reason=None
                if tr.seconds_since_measurement>self.max_unseen_seconds: reason='time_expired'
                elif tr.confirmed_at is None and tr.seconds_since_measurement>self.tentative_seconds: reason='tentative_expired'
                elif tr.confirmed_at is not None and np.sqrt(max(tr.kf.P[0,0],tr.kf.P[1,1]))>self.max_position_std: reason='uncertainty_limit'
            else:
                reason='missed_frame_limit' if tr.missed_frames>self.max_missed else ('tentative_expired' if tr.confirmed_at is None and tr.missed_frames>2 else None)
            if reason: remove(tid,reason)

        # Near-identical detector proposals are one observation, not two ships.
        # Highest-confidence proposal survives; retain original source indices.
        duplicate_indices=set()
        accepted=[]
        for idx in sorted(range(len(detections)), key=lambda i: float(detections[i].get('confidence',detections[i].get('conf',1.))), reverse=True):
            box=detections[idx].get('bbox')
            if box is not None and any(same_vessel_footprint(box,b,.80) for b in accepted):
                duplicate_indices.add(idx)
                events.append({'event':'detection_suppressed','detection_index':idx,'reason':'duplicate_detector_proposal'})
            elif box is not None: accepted.append(box)
        high=[]; low=[]
        for idx,d in enumerate(detections):
            if idx in duplicate_indices: continue
            confidence=float(d.get('confidence',d.get('conf',1.)))
            box=d.get('bbox')
            geometry=box if box is not None else [d.get('cx',0),d.get('cy',0),d.get('w',10),d.get('h',10)]
            if not np.isfinite(geometry).all() or not math.isfinite(confidence):
                events.append({'event':'detection_rejected','detection_index':idx,'reason':'nonfinite_measurement'}); continue
            if box is not None:
                if box[2]<=box[0] or box[3]<=box[1]:
                    events.append({'event':'detection_rejected','detection_index':idx,'reason':'invalid_box'});continue
                # One detector box enclosing two established vessels is not a new identity.
                enclosed=[]
                for tr in self.tracks.values():
                    if tr.confirmed_at is None:continue
                    tb=tr.bbox
                    intersection=max(0.,min(box[2],tb[2])-max(box[0],tb[0]))*max(0.,min(box[3],tb[3])-max(box[1],tb[1]))
                    if intersection/max(1.,tr.w*tr.h)>=.40:enclosed.append(tr)
                if len(enclosed)>=2:
                    events.append({'event':'detection_rejected','detection_index':idx,'reason':'merged_existing_vessels'});continue
            (high if confidence>=self.high_threshold else low if confidence>=self.low_threshold else []).append((idx,d))
        active=[tid for tid,tr in self.tracks.items() if (tr.seconds_since_measurement<=self.recent_seconds if timed else tr.missed_frames<=3)]
        coasting=[tid for tid in self.tracks if tid not in active]
        used=set(); matched={}

        def match(candidates,ids,stage,max_cost):
            gate=(18.4668 if stage==3 else 13.2767) if timed else None
            event_start=len(events)
            pairs=associate_detections_to_tracks([d for _,d in candidates],ids,self.tracks,set(),max_cost,
                    mahalanobis_gate=gate,reject_ambiguous=timed and stage==3,diagnostics=events)
            for event in events[event_start:]:
                event['stage']=stage
                if 'detection_index' in event: event['detection_index']=candidates[event['detection_index']][0]
            stage_counts[stage-1]=len(pairs)
            for local,tid in pairs:
                original,d=candidates[local];tr=self.tracks[tid]
                cost=compute_association_cost(d,tr,gate)
                prior=tr.bbox.copy();gap=tr.seconds_since_measurement
                tr.update(d);tr.matching_stage=stage;tr.matching_cost=cost
                matched[tid]=(original,d);used.add(original)
                associations.append({'track_id':tid,'detection_index':original,'stage':stage,'cost':cost})
                if len(tr.measurement_components)<4: events.append({'event':'partial_measurement','track_id':tid,'reason':'truncated_box_unreliable_axes_not_updated','components':tr.measurement_components})
                if tr.recovered: events.append({'event':'recovered','track_id':tid,'gap_seconds':gap,'stage':stage})
            for tid in ids:
                if tid not in matched and candidates:
                    events.append({'event':'association_unmatched','track_id':tid,'stage':stage,
                                   'reason':'statistical_or_geometry_gate_or_one_to_one_competition'})

        match(high,active,1,.85)
        match(low,[tid for tid in active if tid not in matched],2,.80)
        match([(i,d) for i,d in high if i not in used],coasting,3,.85)
        matched_objects=[self.tracks[tid] for tid in matched]
        created=0
        for idx,d in high:
            if idx in used: continue
            if is_subpart_detection(d,matched_objects,iou_thresh=.25):
                events.append({'event':'detection_suppressed','detection_index':idx,'reason':'contained_deck_subpart'});continue
            # A small almost-contained return is a partial hull observation, not
            # evidence for a second ship occupying the same image footprint.
            coast_objects=[tr for tr in self.tracks.values() if tr.confirmed_at is not None and not tr.observed]
            if is_subpart_detection(d,coast_objects,iou_thresh=.25):
                events.append({'event':'detection_suppressed','detection_index':idx,'reason':'contained_partial_coasting_hull'});continue
            box=d.get('bbox')
            duplicate_candidates=[tr for tr in self.tracks.values()
                                  if box is not None and same_vessel_footprint(box,tr.bbox)]
            if duplicate_candidates:
                # A failed statistical gate must not spawn a second ID on the
                # same footprint. Defer rather than forcing a bad Kalman update.
                events.append({'event':'detection_suppressed','detection_index':idx,
                               'reason':'duplicate_track_birth_deferred',
                               'candidate_track_ids':[tr.track_id for tr in duplicate_candidates]})
                continue
            tid=self.create_track(d);matched[tid]=(idx,d);matched_objects.append(self.tracks[tid]);created+=1
            events.append({'event':'created','track_id':tid,'detection_index':idx,'reason':'no_eligible_unambiguous_existing_match'})
        for tid,tr in self.tracks.items():
            if tid not in matched:
                if inference_ran: tr.hit_streak=0
                events.append({'event':'coasting' if tr.confirmed_at is not None else 'tentative_unobserved',
                               'track_id':tid,'reason':'detector_miss' if inference_ran else 'inference_skipped'})
        output=[]
        for tid,tr in sorted(self.tracks.items()):
            if tid in matched:
                index,d=matched[tid];output.append(tr.to_dict(index,d))
            elif include_predictions and tr.confirmed_at is not None:
                output.append(tr.to_dict())
        snapshots=[tr.to_dict(*(matched.get(tid,(None,None)))) for tid,tr in sorted(self.tracks.items())]
        self.last_diagnostics={'solver':'Hungarian','state_labels':['cx','cy','w','h','vx','vy','vw','vh'],
            'timestamp':now,'dt':dt,'velocity_units':'pixels/second' if timed else 'pixels/update',
            'stage_matches':stage_counts,'high_detections':len(high),'low_detections':len(low),
            'new_tracks':created,'detected_vessels':len(detections),'coasting_tracks':sum(not tr.observed and tr.confirmed_at is not None for tr in self.tracks.values()),
            'confirmed_tracks':sum(tr.observed and tr.confirmed_at is not None for tr in self.tracks.values()),
            'recovered_tracks':sum(tr.recovered for tr in self.tracks.values()),
            'deleted_tracks':deleted,'scene_cut':bool(scene_cut),'camera_status':camera_status,
            'inference_ran':bool(inference_ran),'events':events,'associations':associations,'tracks':snapshots}
        return output
