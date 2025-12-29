import pytest
import os
import logging
from openai import OpenAI
from tests import validate_audio_file

logger = logging.getLogger(__name__)

BASIC_TTS_TEXT = "The quick brown fox jumps over the lazy dog. This is a test of the English text to speech generation."

@pytest.mark.parametrize("format", ["wav", "mp3", "flac", "opus", "aac", "pcm"])
def test_tts_basic(format, sync_client, output_dir, common_constants):
    """Test basic TTS generation for all supported formats."""
    
    output_file = output_dir / f"test_tts.{format}"
    
    logger.info(f"Generating audio file: {output_file}")
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=BASIC_TTS_TEXT,
            voice=common_constants["VOICE"],
            response_format=format
        ) as response:
            response.stream_to_file(str(output_file))
        
        logger.info(f"Success! Audio file saved: {output_file}")
        
        if format == "pcm":
            logger.info("PCM format: 24kHz, 16-bit signed, little-endian, mono")
        
        assert validate_audio_file(str(output_file), format), f"Audio validation failed for {format}"
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
