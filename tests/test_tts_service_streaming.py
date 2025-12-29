#!/usr/bin/env python3
"""Test TTS streaming with SSE events."""

import requests
import json
import time
import base64
import os
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tts_streaming():
    """Test TTS streaming with SSE format and verify continuous streaming."""
    
    base_url = "http://localhost:8000"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    output_file = os.path.join(output_dir, "test_tts_service_streaming.wav")
    
    logger.info(f"Generating audio file: {output_file}")
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code != 200:
            logger.error("Server is running but not responding correctly")
            return False
    except requests.exceptions.RequestException:
        logger.error("Server is not running at http://localhost:8000")
        logger.error("Start it with: ./start.sh")
        return False
    
    # Read text from file and truncate to desired length
    script_dir = os.path.dirname(os.path.abspath(__file__))
    text_file_path = os.path.join(script_dir, "..", "test_text.txt")
    
    try:
        with open(text_file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        
        # Use first 4000 characters to stay within 4096 limit
        text_length = 4000
        long_text = full_text[:text_length]
        
    except FileNotFoundError:
        logger.error("test_text.txt not found")
        return False
    
    request_data = {
        "model": "hexgrad/Kokoro-82M",
        "input": long_text,
        "voice": "af_sarah",
        "response_format": "wav",
        "stream_format": "sse",
        "stream": True
    }
    
    logger.info("Sending streaming TTS request...")
    logger.info(f"Text length: {len(request_data['input'])} characters")
    
    try:
        response = requests.post(
            f"{base_url}/v1/audio/speech",
            json=request_data,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Server returned status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
        
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
                                
                                # Write immediately to file
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

        logger.info(f"Audio saved to: {output_file} (WAV format from server chunks)")
        combined_audio = b''.join(audio_chunks)
        logger.info(f"File size: {len(combined_audio)} bytes")
        num_samples = (len(combined_audio) - 44) // 2
        logger.info(f"Duration: {num_samples / 24000:.2f} seconds")

        logger.info("=" * 60)
        logger.info("Test Results:")
        logger.info(f"- Delta events received: {len(delta_events)}")
        logger.info(f"- Done event received: {done_event is not None}")

        # Validate results
        if len(delta_events) == 0:
            logger.error("No delta events received")
            return False
        
        if len(delta_events) == 1:
            logger.warning("Only one delta event - streaming may not be continuous")
        else:
            logger.info(f"PASS: Received {len(delta_events)} delta events - streaming is continuous")
        
        if not done_event:
            logger.error("No done event received")
            return False
        else:
            logger.info("PASS: Done event received")
        
        # Check timing between chunks
        if len(delta_events) > 1:
            logger.info("Timing analysis:")
            for i in range(1, len(delta_events)):
                time_diff = delta_events[i]['timestamp'] - delta_events[i-1]['timestamp']
                logger.info(f"  Chunk {i-1} -> {i}: {time_diff:.3f}s")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 60 seconds")
        return False
    except Exception as e:
        logger.error(f"{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tts_streaming()
    if success:
        logger.info("PASS: Test passed!")
    else:
        logger.error("FAIL: Test failed!")
        exit(1)
