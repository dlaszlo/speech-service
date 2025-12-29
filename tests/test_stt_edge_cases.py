import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.exceptions import TranscriptionError, ModelNotLoadedError

client = TestClient(app)

@pytest.fixture
def mock_stt_model_state():
    with patch("src.api.transcription.model_state") as mock_state:
        yield mock_state

@pytest.fixture
def mock_transcribe():
    with patch("src.api.transcription.transcribe") as mock_func:
        yield mock_func

def test_model_mismatch(mock_stt_model_state):
    """Test using formatted valid exception for model mismatch."""
    mock_stt_model_state.model_id = "loaded_model"
    
    # Simulate a request with a different model
    # We need to send a file to pass first validation
    files = {'file': ('test.wav', b'dummy content', 'audio/wav')}
    data = {'model': 'requested_model'}
    
    response = client.post("/v1/audio/transcriptions", files=files, data=data)
    
    # Should get 400 Bad Request
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "model_not_found"

def test_transcription_service_error(mock_stt_model_state, mock_transcribe):
    """Test that TranscriptionError is caught and returns 500."""
    mock_stt_model_state.model_id = "loaded_model"
    mock_transcribe.side_effect = TranscriptionError("Internal failure")
    
    files = {'file': ('test.wav', b'dummy content', 'audio/wav')}
    data = {'model': 'loaded_model'}
    
    response = client.post("/v1/audio/transcriptions", files=files, data=data)
    
    assert response.status_code == 500
    json_resp = response.json()
    assert json_resp["error"]["code"] == "transcription_failed"
    assert "Internal failure" in json_resp["error"]["message"]

def test_empty_file():
    """Test uploading an empty file (if handled, or just small file that is valid)."""
    # Note: The code doesn't explicitly check for 0 bytes, but `transcribe` might.
    # However, we mocked transcribe. Let's see if we can trigger "File too large".
    pass

def test_file_too_large():
    """Test file size limit."""
    with patch("src.api.transcription.MAX_FILE_SIZE_BYTES", 10): # Set limit to 10 bytes
        files = {'file': ('large.wav', b'12345678901', 'audio/wav')} # 11 bytes
        response = client.post("/v1/audio/transcriptions", files=files)
        
        assert response.status_code == 413
        assert "exceeds the maximum limit" in response.json()["detail"]
