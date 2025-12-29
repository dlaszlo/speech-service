#!/usr/bin/env python3
"""Test MP3 TTS with OpenAI client."""

from openai import OpenAI
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tts():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "test_tts_mp3.mp3")
    
    logger.info(f"Generating audio file: {output_file}")
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )

    logger.info("Sending TTS Request...")
    
    try:
        with client.audio.speech.with_streaming_response.create(
            model="hexgrad/Kokoro-82M",
            input="The quick brown fox jumps over the lazy dog. This is a test of the English text to speech generation.",
            voice="af_sarah",
            response_format="mp3"
        ) as response:
            response.stream_to_file(output_file)
        
        logger.info(f"Success! Audio file saved: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_tts()
    if not success:
        exit(1)
