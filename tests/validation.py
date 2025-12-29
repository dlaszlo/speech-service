import os
import logging

logger = logging.getLogger(__name__)

def validate_audio_file(file_path, format):
    """Validate audio file exists and has minimum size."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    size = os.path.getsize(file_path)
    min_sizes = {"wav": 44, "mp3": 100, "pcm": 1000, "aac": 100, "opus": 100, "flac": 100}
    
    if size < min_sizes.get(format, 100):
        logger.error(f"File too small: {size} bytes (min: {min_sizes[format]})")
        return False
    
    return True

def validate_transcription(text, min_length=10, expected_keywords=None):
    """Validate transcription quality."""
    if not text or len(text.strip()) < min_length:
        logger.error(f"Transcription too short: {len(text)} chars")
        return False
    
    if expected_keywords:
        text_lower = text.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in text_lower]
        if not found_keywords:
            logger.warning(f"No expected keywords found in transcription")
            return False
    
    return True

def validate_chunk_count(count, min_expected=2):
    """Validate streaming received chunks."""
    if count == 0:
        logger.error("No chunks received")
        return False
    if count < min_expected:
        logger.error(f"Expected at least {min_expected} chunks, received {count}")
        return False
    else:
        logger.info(f"PASS: Received {count} chunks")
    return True

def validate_sse_delta_events(count, min_expected=2):
    """Validate SSE delta events."""
    if count == 0:
        logger.error("No delta events received")
        return False
    if count < min_expected:
        logger.error(f"Expected at least {min_expected} delta events, received {count}")
        return False
    else:
        logger.info(f"PASS: Received {count} delta events - streaming is continuous")
    return True

def validate_sse_done_event(event):
    """Validate SSE done event."""
    if not event:
        logger.error("No done event received")
        return False
    logger.info("PASS: Done event received")
    return True

def calculate_audio_duration(file_size, format):
    """Calculate audio duration based on format and file size."""
    if format == "wav":
        num_samples = (file_size - 44) // 2
        return num_samples / 24000
    elif format == "pcm":
        return file_size / 48000
    else:
        return file_size / 10000  # Rough estimate for compressed formats
