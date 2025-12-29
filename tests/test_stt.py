import pytest
import os
import logging
from openai import OpenAI
from tests import validate_audio_file, validate_transcription

logger = logging.getLogger(__name__)

EXPECTED_KEYWORDS = ["fox", "dog", "quick", "brown"]

@pytest.mark.parametrize("format", ["wav", "mp3"])
def test_stt(format, sync_client, output_dir, common_constants):
    """Test STT transcription for WAV and MP3 formats."""
    
    audio_file = output_dir / f"test_tts.{format}"
    transcription_file = output_dir / f"test_stt_{format}.txt"
    
    logger.info(f"Checking audio file: {audio_file}")
    
    if not os.path.exists(audio_file):
        logger.info(f"Audio file not found, generating with TTS...")
        basic_tts_text = "The quick brown fox jumps over the lazy dog. This is a test of English text to speech generation."
        
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=basic_tts_text,
            voice=common_constants["VOICE"],
            response_format=format
        ) as response:
            response.stream_to_file(str(audio_file))
        
        logger.info(f"Audio file generated: {audio_file}")
    
    assert validate_audio_file(str(audio_file), format), f"Audio validation failed for {format}"
    logger.info(f"Reading audio file: {audio_file}")

    logger.info("Sending STT Request (Transcription)...")
    
    try:
        with open(audio_file, "rb") as f:
            response = sync_client.audio.transcriptions.create(
                model=common_constants["STT_MODEL"],
                file=f
            )
        
        logger.info(f"Success! Response received: {response.text}")
        
        with open(transcription_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        logger.info(f"Transcription saved to: {transcription_file}")
        
        assert validate_transcription(response.text, min_length=20, expected_keywords=EXPECTED_KEYWORDS), "Transcription validation failed"
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise
