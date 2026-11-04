from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import pytest
from models.vlm_guard import RequestGuard
from models.groq_vlm import GroqVLM

def response():
    return NS(usage=NS(total_tokens=2491,prompt_tokens=2400,completion_tokens=91),
              choices=[NS(message=NS(content='{"label":"Frigate","confidence":0.8,"reasoning":"Visible hull"}'))])

def limited():
    err=Exception('sensitive request must never be logged')
    err.status_code=429;err.response=NS(headers={'retry-after':'1054'})
    return err

def setup_guard():
    now=[0.0];guard=RequestGuard(clock=lambda:now[0]);client=Mock()
    client.chat.completions.create.return_value=response()
    return guard,client,now

def test_100_identical_requests_use_one_call():
    guard,client,now=setup_guard()
    for _ in range(100):guard.request(client,{'model':'test','messages':[]})
    assert client.chat.completions.create.call_count==1
    assert guard.stats['cache_hits']==99 and guard.stats['tokens']==2491

def test_429_shared_cooldown_and_retry_without_sleep(caplog):
    guard,client,now=setup_guard();client.chat.completions.create.side_effect=limited()
    for i in range(100):
        with pytest.raises(RuntimeError):guard.request(client,{'messages':[str(i)]})
    assert client.chat.completions.create.call_count==1
    assert guard.stats['rate_limit_events']==1 and guard.stats['suppressed']==99
    assert 'sensitive' not in caplog.text
    now[0]=1055;client.chat.completions.create.side_effect=None
    guard.request(client,{'messages':['retry']})
    assert client.chat.completions.create.call_count==2

def test_retry_body_and_bounded_missing_guidance():
    guard,_,_=setup_guard();err=Exception('Please try again in 17m34.944s.')
    assert guard._retry_delay(err)==pytest.approx(1054.944)
    guard.failures=30
    assert guard._retry_delay(Exception('unknown'))==300

def test_budget_and_interval():
    guard,client,now=setup_guard();guard.daily_budget=3000
    guard.request(client,{'messages':['a']})
    now[0]=100
    with pytest.raises(RuntimeError):guard.request(client,{'messages':['b']})
    assert client.chat.completions.create.call_count==1

def test_instances_share_guard():
    assert GroqVLM().guard is GroqVLM().guard

def test_real_video_continues_during_429(tmp_path):
    from backend.main import pipeline
    guard,client,now=setup_guard();client.chat.completions.create.side_effect=limited()
    vlm=GroqVLM();vlm.guard=guard;vlm.client=client;vlm.model='test'
    local=pipeline.classifier.classify
    def uncertain(*args,**kwargs):
        result=local(*args,**kwargs);result['uncertain']=True
        return result
    with patch.object(pipeline,'vlm',vlm),patch.object(pipeline.classifier,'classify',side_effect=uncertain):
        result=pipeline.drone_video('data/test_mp4/Destroyer1.mp4',sample_every=2,
                                   output_dir=tmp_path,write_analytics=False)
    assert result['processed_frames']==120
    assert result['unique_track_count']==2
    assert not [f for f in result['frames'] if f['processing_mode']=='error']
    assert result['classifier_calls']>0
    assert any(t.get('classification',{}).get('vlm',{}).get('source')=='unavailable'
               for f in result['frames'] for t in f['tracks'] if t.get('classification'))
    assert client.chat.completions.create.call_count==1
    assert guard.stats['rate_limit_events']==1
    print('MEASURED video_frames=120 actual_Groq_calls=1 counters=',dict(guard.stats))

def test_track_reasoning_cached_without_repeated_evidence():
    from pipeline.orchestrator import OATrackPipeline
    import numpy as np
    pipeline=OATrackPipeline.__new__(OATrackPipeline)
    pipeline.detector=Mock();pipeline.detector.crop.return_value=np.zeros((20,20,3),dtype=np.uint8)
    pipeline._current_frame=np.zeros((30,30,3),dtype=np.uint8)
    pipeline.classifier=Mock();pipeline.classifier.classify.side_effect=lambda *a,**k:dict(label='Frigate',confidence=.6,uncertain=True,vlm_reasoned=False)
    pipeline.vlm=Mock();pipeline.vlm.guard.last_source='fresh'
    pipeline.vlm.classify_vessel.return_value=dict(label='Frigate',confidence=.8,reasoning='Visible hull')
    pipeline.track_vlm_cache={};pipeline.video_vlm_enabled=True
    pipeline._update_track_classification=Mock(return_value={})
    fresh,_=pipeline._classify_track({'track_id':1,'hits':3},{'bbox':[0,0,20,20]},3)
    for frame in range(4,104):
        cached,_=pipeline._classify_track({'track_id':1,'hits':frame},{'bbox':[0,0,20,20]},frame)
        assert cached['vlm']['source']=='cached' and not cached['vlm_reasoned']
    assert fresh['vlm']['source']=='fresh' and not fresh['vlm_reasoned']
    assert fresh['label']=='Frigate'  # VLM remains advisory, local classifier unchanged
    assert pipeline.vlm.classify_vessel.call_count==1
    assert pipeline.vlm.guard.track_cache_hit.call_count==100
