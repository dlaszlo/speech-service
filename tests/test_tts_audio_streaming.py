import pytest
import os
import logging
import time
from typing import List
from openai import AsyncOpenAI
from tests import validate_audio_file, validate_chunk_count, calculate_audio_duration

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("format", ["wav", "mp3", "flac", "opus", "aac", "pcm"])
@pytest.mark.asyncio
async def test_tts_audio_streaming(format, async_client, output_dir, test_text, common_constants):
    """Test OpenAI async audio streaming for all supported formats."""
    
    output_file = output_dir / f"test_tts_audio.{format}"
    
    logger.info(f"Generating audio file: {output_file}")
    logger.info(f"Text length: {len(test_text)} characters")
    
    try:
        logger.info("Sending streaming TTS request...")
        async with async_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=test_text,
            voice=common_constants["VOICE"],
            response_format=format
        ) as response:
            
            logger.info("Receiving audio chunks...")
            chunk_count = 0
            chunk_times: List[float] = []
            audio_chunks: List[bytes] = []

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
        
        duration = calculate_audio_duration(file_size, format)
        logger.info(f"Duration: {duration:.2f} seconds")

        logger.info("=" * 60)
        logger.info("Test Results:")
        logger.info(f"- Chunks received: {chunk_count}")

        assert validate_chunk_count(chunk_count), "Chunk validation failed"
        
        if chunk_count > 1:
            logger.info("Timing analysis:")
            for i in range(1, len(chunk_times)):
                time_diff = chunk_times[i] - chunk_times[i-1]
                logger.info(f"  Chunk {i-1} -> {i}: {time_diff:.3f}s")
        
        assert validate_audio_file(str(output_file), format), f"Audio validation failed for {format}"
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
