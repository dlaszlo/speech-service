import pytest
import os
import logging
import time
from typing import List
from tests import validate_audio_file, validate_chunk_count, calculate_audio_duration

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("format", ["wav", "mp3", "flac", "opus", "aac", "pcm"])
def test_tts_audio_streaming(format, api_client, output_dir, test_text, common_constants, caplog):
    """Test audio streaming and prove server-side yielding using logs."""
    # Ensure caplog is empty before starting to guarantee distinct test isolation
    caplog.clear()
    assert len(caplog.records) == 0, "Caplog should be empty at the start of the test"

    caplog.set_level(logging.INFO)
    output_file = output_dir / f"test_tts_audio.{format}"
    
    logger.info(f"Generating audio file: {output_file}")
    
    request_data = {
        "model": common_constants["TTS_MODEL"],
        "input": test_text,
        "voice": common_constants["VOICE"],
        "response_format": format,
    }
    
    try:
        logger.info("Sending streaming TTS request...")
        with api_client.stream("POST", "/v1/audio/speech", json=request_data) as response:
            assert response.status_code == 200
            # Streaming responses should not have a Content-Length header
            assert "content-length" not in response.headers
            
            logger.info("Receiving audio chunks...")
            chunk_count = 0
            audio_chunks: List[bytes] = []

            with open(output_file, 'wb') as f:
                # Use chunk_size=None to receive data as it is delivered by the transport
                for chunk in response.iter_bytes(chunk_size=None):
                    if not chunk:
                        continue
                    chunk_count += 1
                    audio_chunks.append(chunk)
                    f.write(chunk)
        
        # PROOF OF STREAMING:
        # We check the server-side logs captured during the request.
        # The tts_service logs "[AUDIO] Sending chunk #X" for each yield.
        sending_logs = [rec.message for rec in caplog.records if "[AUDIO] Sending chunk" in rec.message]
        
        logger.info(f"Server-side stream events: {len(sending_logs)}")
        for log in sending_logs:
            logger.info(f"  Captured log: {log}")

        # Assert that the server actually yielded multiple times
        assert len(sending_logs) >= 2, f"Server did not yield multiple chunks (only {len(sending_logs)} found in logs)"
        
        # Note: chunk_count (client-side) might still be 1 due to TestClient's 
        # internal buffering, but sending_logs proves the server was streaming.
        logger.info(f"Success! Server-side streaming verified with {len(sending_logs)} chunks.")
        assert validate_audio_file(str(output_file), format)

        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
