"""Separate current lifecycle state from all-time classified track history."""
def build_track_registry(frames, classifications):
    registry={}
    for frame in frames:
        diag=frame.get('tracking_diagnostics',{})
        for tr in diag.get('tracks',[]):
            tid=str(tr['track_id']);row=registry.setdefault(tid,{'track_id':tr['track_id'],'created_frame':frame['frame_index']})
            row.update(tracking_state=tr['state'],lifecycle_state=tr['lifecycle_state'],
                       tracking_observations=tr['hits'],confirmed_identity=tr.get('confirmed_identity',False),
                       confirmed_at=tr.get('confirmed_at'),last_bbox=tr.get('bbox'),
                       seconds_since_measurement=tr.get('seconds_since_measurement',0),prediction_reason=tr.get('prediction_reason'))
            if tr.get('observed'):
                row['last_measurement_frame']=frame['frame_index']
        for event in diag.get('events',[]):
            tid=str(event.get('track_id'))
            if tid in registry and event['event']=='deleted':
                registry[tid].update(lifecycle_state='deleted',tracking_state='deleted',
                                     deletion_frame=frame['frame_index'],deletion_reason=event.get('reason'))
    for tid,row in registry.items():
        classification = classifications.get(tid,{'label':'Vessel','display_label':'Vessel (unclassified)',
                   'stability':0.,'observations':0,'classification_status':'unclassified','uncertain':True})
        # Lifecycle comes from tracker snapshots, never classification history.
        for key in ('label','display_label','stability','observations','classification_status','uncertain','candidates','vlm','last_seen_frame'):
            if key in classification: row[key]=classification[key]
        row['is_current']=row.get('lifecycle_state')!='deleted'
        row['record_scope']='current' if row['is_current'] else 'historical'
    rows=list(registry.values());current=[r for r in rows if r['is_current']]
    counts={'current_tracks':len(current),
            'confirmed_detected':sum(r['confirmed_identity'] and r['lifecycle_state'] in ('confirmed','recovered') for r in current),
            'coasting':sum(r['lifecycle_state']=='coasting' for r in current),
            'tentative':sum(r['lifecycle_state']=='tentative' for r in current),
            'deleted_history':sum(not r['is_current'] for r in rows),
            'confirmed_identities_total':sum(r['confirmed_identity'] for r in rows),
            'all_time_tracks':len(rows)}
    return registry,counts
