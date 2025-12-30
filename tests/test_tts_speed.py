import pytest
import logging
from openai import OpenAI
from tests import validate_audio_file

logger = logging.getLogger(__name__)

BASIC_TTS_TEXT = "The quick brown fox jumps over the lazy dog."

class TestTTSSpeed:
    """Test speed parameter functionality in TTS."""

    @pytest.mark.parametrize("speed", [0.25, 0.5, 1.0, 2.0, 4.0])
    def test_tts_valid_speeds(self, speed, sync_client, output_dir, common_constants):
        """Test TTS generation with valid speed values."""
        output_file = output_dir / f"test_tts_speed_{speed}.mp3"
        
        logger.info(f"Testing TTS with speed={speed}")
        
        try:
            with sync_client.audio.speech.with_streaming_response.create(
                model=common_constants["TTS_MODEL"],
                input=BASIC_TTS_TEXT,
                voice=common_constants["VOICE"],
                response_format="mp3",
                speed=speed
            ) as response:
                response.stream_to_file(str(output_file))
            
            logger.info(f"Success! Audio file saved: {output_file}")
            assert validate_audio_file(str(output_file), "mp3"), f"Audio validation failed for speed={speed}"
            
        except Exception as e:
            logger.error(f"Error occurred with speed={speed}: {e}")
            raise

    @pytest.mark.parametrize("invalid_speed", [0.0, 0.24, -0.5, 4.1, 5.0, 10.0])
    def test_tts_invalid_speeds(self, invalid_speed, api_client, common_constants):
        """Test TTS generation with invalid speed values."""
        request_data = {
            "model": common_constants["TTS_MODEL"],
            "input": BASIC_TTS_TEXT,
            "voice": common_constants["VOICE"],
            "response_format": "mp3",
            "speed": invalid_speed
        }
        
        logger.info(f"Testing invalid speed={invalid_speed}")
        
        try:
            response = api_client.post("/v1/audio/speech", json=request_data)
            
            assert response.status_code == 400 or response.status_code == 422, \
                f"Expected 400 or 422 for invalid speed={invalid_speed}, got {response.status_code}"
            
            logger.info(f"Correctly rejected invalid speed={invalid_speed} with status {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error occurred with invalid speed={invalid_speed}: {e}")
            raise

    def test_tts_default_speed(self, sync_client, output_dir, common_constants):
        """Test TTS generation without specifying speed (should use default 1.0)."""
        output_file = output_dir / "test_tts_default_speed.mp3"
        
        logger.info("Testing TTS with default speed (1.0)")
        
        try:
            with sync_client.audio.speech.with_streaming_response.create(
                model=common_constants["TTS_MODEL"],
                input=BASIC_TTS_TEXT,
                voice=common_constants["VOICE"],
                response_format="mp3"
            ) as response:
                response.stream_to_file(str(output_file))
            
            logger.info(f"Success! Audio file saved: {output_file}")
            assert validate_audio_file(str(output_file), "mp3"), "Audio validation failed for default speed"
            
        except Exception as e:
            logger.error(f"Error occurred with default speed: {e}")
            raise

    @pytest.mark.parametrize("speed", [0.25, 1.0, 4.0])
    def test_tts_speed_streaming(self, speed, api_client, output_dir, common_constants):
        """Test TTS streaming with different speed values."""
        output_file = output_dir / f"test_tts_streaming_speed_{speed}.wav"
        
        logger.info(f"Testing TTS streaming with speed={speed}")
        
        request_data = {
            "model": common_constants["TTS_MODEL"],
            "input": BASIC_TTS_TEXT,
            "voice": common_constants["VOICE"],
            "response_format": "wav",
            "speed": speed
        }
        
        try:
            with api_client.stream("POST", "/v1/audio/speech", json=request_data) as response:
                assert response.status_code == 200
                
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=None):
                        if chunk:
                            f.write(chunk)
            
            logger.info(f"Success! Audio file saved: {output_file}")
            assert validate_audio_file(str(output_file), "wav"), f"Audio validation failed for speed={speed}"
            
        except Exception as e:
            logger.error(f"Error occurred with speed={speed}: {e}")
            raise

    @pytest.mark.parametrize("speed", [0.5, 1.0, 2.0])
    def test_tts_speed_sse_streaming(self, speed, output_dir, common_constants, api_client):
        """Test TTS SSE streaming with different speed values."""
        output_file = output_dir / f"test_tts_sse_speed_{speed}.wav"
        
        logger.info(f"Testing TTS SSE streaming with speed={speed}")
        
        request_data = {
            "model": common_constants["TTS_MODEL"],
            "input": BASIC_TTS_TEXT,
            "voice": common_constants["VOICE"],
            "response_format": "wav",
            "stream_format": "sse",
            "speed": speed
        }
        
        try:
            with api_client.stream("POST", "/v1/audio/speech", json=request_data) as response:
                assert response.status_code == 200
                
                audio_chunks = []
                for line in response.iter_lines():
                    if line:
                        if isinstance(line, bytes):
                            line_str = line.decode('utf-8')
                        else:
                            line_str = line
                        
                        if line_str.startswith('data: '):
                            import json
                            import base64
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('type') == 'speech.audio.delta':
                                    audio_data = data.get('audio', '')
                                    if audio_data:
                                        audio_bytes = base64.b64decode(audio_data)
                                        audio_chunks.append(audio_bytes)
                            except (json.JSONDecodeError, ValueError):
                                continue
                
                with open(output_file, 'wb') as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
            
            logger.info(f"Success! Audio file saved: {output_file}")
            assert validate_audio_file(str(output_file), "wav"), f"Audio validation failed for speed={speed}"
            
        except Exception as e:
            logger.error(f"Error occurred with speed={speed}: {e}")
            raise
