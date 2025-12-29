import pytest
import logging
from pathlib import Path
from openai import OpenAI, AsyncOpenAI

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

@pytest.fixture
def sync_client():
    """Return synchronous OpenAI client."""
    return OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

@pytest.fixture
def async_client():
    """Return asynchronous OpenAI client."""
    return AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="dummy")

@pytest.fixture
def common_constants():
    """Return common test constants."""
    return {
        "BASE_URL": "http://localhost:8000",
        "API_URL": "http://localhost:8000/v1",
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
