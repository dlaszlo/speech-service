#!/usr/bin/env python3
"""Test MP3 TTS audio streaming with OpenAI client."""

import asyncio
import os
import logging
import time
from typing import List

from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tts_audio_streaming():
    """Test MP3 TTS audio streaming with OpenAI client and save to file."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "test_tts_audio_mp3.mp3")
    
    logger.info(f"Generating audio file: {output_file}")
    
    # Read text from file
    text_file_path = os.path.join(script_dir, "test_text.txt")
    try:
        with open(text_file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        long_text = full_text[:4000]
    except FileNotFoundError:
        logger.error("test_text.txt not found")
        return False
    
    logger.info(f"Text length: {len(long_text)} characters")
    
    client = AsyncOpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )
    
    try:
        logger.info("Sending streaming TTS request...")
        async with client.audio.speech.with_streaming_response.create(
            model="hexgrad/Kokoro-82M",
            input=long_text,
            voice="af_sarah",
            response_format="mp3"
        ) as response:
            
            logger.info("Receiving audio chunks...")
            chunk_count = 0
            chunk_times: List[float] = []
            audio_chunks: List[bytes] = []

            # Stream to file
            with open(output_file, 'wb') as f:
                async for chunk in response.iter_bytes():
                    chunk_size = len(chunk)
                    chunk_count += 1
                    current_time = time.time()
                    chunk_times.append(current_time)
                    audio_chunks.append(chunk)
                    
                    logger.info(f"[CHUNK] Received chunk #{chunk_count}, size: {chunk_size} bytes")
                    f.write(chunk)
        
        file_size = os.path.getsize(output_file)
        logger.info(f"Success! Audio file saved: {output_file} ({file_size} bytes)")
        
        logger.info("=" * 60)
        logger.info("Test Results:")
        logger.info(f"- Chunks received: {chunk_count}")

        if chunk_count == 0:
            logger.error("No chunks received")
            return False
            
        if chunk_count == 1:
            logger.warning("Only one chunk received - streaming might not be working as expected (unless short text)")
        else:
            logger.info(f"PASS: Received {chunk_count} chunks - streaming is active")

        # Check timing between chunks
        if len(chunk_times) > 1:
            logger.info("Timing analysis:")
            for i in range(1, len(chunk_times)):
                time_diff = chunk_times[i] - chunk_times[i-1]
                logger.info(f"  Chunk {i-1} -> {i}: {time_diff:.3f}s")
                
        return True
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tts_audio_streaming())
    if success:
        logger.info("PASS: Test passed!")
    else:
        logger.error("FAIL: Test failed!")
        exit(1)
