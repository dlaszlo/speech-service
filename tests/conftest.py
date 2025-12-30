import pytest
import logging
from pathlib import Path
from openai import OpenAI
from fastapi.testclient import TestClient

# Import the FastAPI app
from src.main import app

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for all tests."""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s'
    )

@pytest.fixture(scope="session")
def output_dir():
    """Create and return output directory."""
    path = Path(__file__).parent / "output"
    path.mkdir(exist_ok=True)
    return path

@pytest.fixture(scope="session")
def api_client():
    """
    Synchronous TestClient acting as the HTTP transport.
    The OpenAI client uses this to make requests directly to the app.
    Using context manager ensures lifespan events (startup/shutdown) are triggered.
    """
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sync_client(api_client):
    """
    Return synchronous OpenAI client configured to use TestClient.
    This runs entirely in-process without a separate server.
    """
    return OpenAI(
        base_url="http://testserver/v1",
        api_key="dummy",
        http_client=api_client
    )

@pytest.fixture
def common_constants():
    """Return common test constants."""
    return {
        "BASE_URL": "http://testserver",
        "API_URL": "http://testserver/v1",
        "API_KEY": "dummy",
        "TTS_MODEL": "hexgrad/Kokoro-82M",
        "STT_MODEL": "Systran/faster-distil-whisper-small.en",
        "VOICE": "af_sarah"
    }

@pytest.fixture
def test_text():
    """Return long text for streaming tests."""
    text_path = Path(__file__).parent / "test_text.txt"
    return text_path.read_text(encoding="utf-8")[:1000]
