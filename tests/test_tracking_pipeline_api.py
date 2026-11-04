"""Real local API integration; external VLM inference is explicitly excluded."""
from pathlib import Path
from unittest.mock import patch
import cv2
import pytest
from fastapi.testclient import TestClient
from backend import main as backend


def test_readonly_health_and_presets_compatibility():
    with TestClient(backend.app) as client:
        for path in ['/health','/drone/presets','/satellite/presets']:
            response=client.get(path);assert response.status_code==200
            assert isinstance(response.json(),dict)


def test_original_cloud_video_upload_and_download_with_predictions():
    path=Path('data/test_mp4/Destroyer1.mp4')
    if not path.exists():pytest.skip('Original cloud video unavailable')
    original=backend.pipeline.drone_video
    def local_processing(*args,**kwargs):
        return original(*args,**kwargs,write_analytics=False,vlm_enabled=False)
    with patch.object(backend.pipeline,'drone_video',side_effect=local_processing),TestClient(backend.app) as client:
        with path.open('rb') as f:
            response=client.post('/drone/video',files={'file':(path.name,f,'video/mp4')},data={'sample_every':'2'})
        assert response.status_code==200
        data=response.json();assert data['status']=='success'
        assert not [fr for fr in data['frames'] if fr['processing_mode']=='error']
        assert data['unique_track_count']==2
        assert data['tracking_velocity_units']=='pixels/second'
        predictions=[t for fr in data['frames'] for t in fr['tracks'] if not t['observed']]
        assert predictions and all(t['classification'] is None for t in predictions)
        assert any(t['recovered'] for fr in data['frames'] for t in fr['tracks'])
        assert Path(data['tracking_diagnostic_csv']).exists()
        download=client.get(data['annotated_video_url']);assert download.status_code==200
        assert download.headers['content-type']=='video/mp4'
        cap=cv2.VideoCapture(data['annotated_video_path']);assert cap.isOpened()
        assert round(cap.get(cv2.CAP_PROP_FPS))==12
        assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==data['processed_frames'];cap.release()


def test_satellite_upload_detection_still_works_offline():
    path=Path('data/vhrv/vhrv/images/test/vhrv_00050.jpg')
    if not path.exists():pytest.skip('Satellite integration image unavailable')
    with patch.object(backend.pipeline.vlm,'generate_briefing',return_value={'status':'DISABLED','text':'External VLM excluded from offline test'}),TestClient(backend.app) as client:
        with path.open('rb') as f:
            response=client.post('/satellite/detect',files={'file':(path.name,f,'image/jpeg')})
        assert response.status_code==200
        data=response.json();assert data['status']=='success' and data['ship_count']>=1
        assert client.get(data['annotated_image_url']).status_code==200
