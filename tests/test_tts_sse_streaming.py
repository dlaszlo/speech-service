import pytest
import requests
import json
import time
import base64
import os
import logging
from typing import List
from tests import validate_audio_file, validate_sse_delta_events, validate_sse_done_event, calculate_audio_duration

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("format", ["wav", "mp3", "flac", "opus", "aac", "pcm"])
def test_tts_sse_streaming(format, output_dir, test_text, common_constants):
    """Test SSE streaming for all supported formats."""
    
    output_file = output_dir / f"test_tts_sse.{format}"
    base_url = common_constants["BASE_URL"]
    
    logger.info(f"Generating audio file: {output_file}")
    logger.info(f"Text length: {len(test_text)} characters")
    
    request_data = {
        "model": common_constants["TTS_MODEL"],
        "input": test_text,
        "voice": common_constants["VOICE"],
        "response_format": format,
        "stream_format": "sse"
    }
    
    logger.info("Sending streaming TTS request...")
    
    try:
        response = requests.post(
            f"{base_url}/v1/audio/speech",
            json=request_data,
            stream=True,
            timeout=60
        )
        
        assert response.status_code == 200, f"Server returned status {response.status_code}: {response.text}"
        
        logger.info("Receiving SSE events...")

        delta_events: List[dict] = []
        done_event = None
        audio_chunks: List[bytes] = []

        with open(output_file, 'wb') as f:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')

                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            event_type = data.get('type')

                            if event_type == 'speech.audio.delta':
                                audio_data = data.get('audio', '')
                                delta_events.append({
                                    'audio_size': len(audio_data),
                                    'timestamp': time.time()
                                })
                                logger.info(f"[DELTA] Audio chunk #{len(delta_events)}, size: {len(audio_data)} chars")

                                audio_bytes = base64.b64decode(audio_data)
                                audio_chunks.append(audio_bytes)
                                
                                f.write(audio_bytes)

                            elif event_type == 'speech.audio.done':
                                done_event = data
                                usage = data.get('usage', {})
                                logger.info(f"[DONE] Stream complete")
                                logger.info(f"       Input tokens: {usage.get('input_tokens')}")
                                logger.info(f"       Output tokens: {usage.get('output_tokens')}")
                                logger.info(f"       Total tokens: {usage.get('total_tokens')}")

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON: {e}")
                            continue

        combined_audio = b''.join(audio_chunks)
        logger.info(f"Audio saved to: {output_file} ({len(combined_audio)} bytes")
        
        duration = calculate_audio_duration(len(combined_audio), format)
        logger.info(f"Duration: {duration:.2f} seconds")

        logger.info("=" * 60)
        logger.info("Test Results:")
        logger.info(f"- Delta events received: {len(delta_events)}")
        logger.info(f"- Done event received: {done_event is not None}")

        assert validate_sse_delta_events(len(delta_events)), "SSE delta events validation failed"
        assert validate_sse_done_event(done_event), "SSE done event validation failed"
        assert validate_audio_file(str(output_file), format), f"Audio validation failed for {format}"
        
        if len(delta_events) > 1:
            logger.info("Timing analysis:")
            for i in range(1, len(delta_events)):
                time_diff = delta_events[i]['timestamp'] - delta_events[i-1]['timestamp']
                logger.info(f"  Chunk {i-1} -> {i}: {time_diff:.3f}s")
        
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 60 seconds")
        raise
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
