import io
import logging
import asyncio
from typing import Optional

from ..core.stt_dependencies import get_model_state
from ..core.exceptions import ModelNotLoadedError, TranscriptionError, TimeoutError as ServiceTimeoutError
from ..core.config import TRANSCRIPTION_TIMEOUT_SECONDS, TRANSCRIPTION_PROCESSING_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)
model_state = get_model_state()

async def transcribe_audio(
    file_content: bytes,
    language: Optional[str],
    prompt: Optional[str],
    temperature: float,
) -> str:
    if not model_state.model:
        logger.error("Transcription requested but no model is loaded.")
        raise ModelNotLoadedError("STT model is not loaded.")

    try:
        logger.info("Starting audio transcription process.")
        
        transcribe_kwargs = {
            "language": language,
            "initial_prompt": prompt,
            "temperature": temperature,
            "beam_size": 5,
            "vad_filter": True,
            "vad_parameters": dict(min_silence_duration_ms=500)
        }
        
        audio_file = None
        try:
            audio_file = io.BytesIO(file_content)

            # faster_whisper's transcribe returns a generator (segments, info)
            segments, info = await asyncio.wait_for(
                asyncio.to_thread(
                    model_state.model.transcribe,
                    audio_file,
                    **transcribe_kwargs
                ),
                timeout=TRANSCRIPTION_TIMEOUT_SECONDS
            )
        finally:
            if audio_file is not None:
                audio_file.close()
        
        logger.info(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

        def process_segments(segs):
            text_list = []
            for segment in segs:
                text_list.append(segment.text)
            return " ".join(text_list).strip()

        full_text = await asyncio.wait_for(
            asyncio.to_thread(process_segments, segments),
            timeout=TRANSCRIPTION_PROCESSING_TIMEOUT_SECONDS
        )
        
        logger.info("Transcription complete.")
        return full_text

    except ModelNotLoadedError:
        raise
    except asyncio.TimeoutError as e:
        logger.error(f"Transcription timed out after {TRANSCRIPTION_TIMEOUT_SECONDS} seconds: {e}")
        raise ServiceTimeoutError(f"Transcription timed out after {TRANSCRIPTION_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        raise TranscriptionError(f"Transcription failed: {str(e)}")