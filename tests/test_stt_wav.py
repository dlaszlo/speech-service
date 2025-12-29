#!/usr/bin/env python3
"""Test WAV STT with OpenAI client."""

from openai import OpenAI
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stt():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    audio_file = os.path.join(output_dir, "test_tts_wav.wav")
    
    logger.info(f"Reading audio file: {audio_file}")
    
    if not os.path.exists(audio_file):
        logger.error(f"The '{audio_file}' file was not found. Run test_tts_wav.py first.")
        return False
    
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )

    logger.info("Sending STT Request (Transcription)...")
    
    try:
        with open(audio_file, "rb") as f:
            response = client.audio.transcriptions.create(
                model="Systran/faster-distil-whisper-small.en",
                file=f
            )
        
        logger.info(f"Success! Response received: {response.text}")
        return True
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_stt()
    if not success:
        exit(1)
