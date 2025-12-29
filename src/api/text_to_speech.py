import logging
import io
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..services.tts_service import synthesize, synthesize_streaming
from ..core.tts_dependencies import get_tts_model_state
from ..core.exceptions import ModelNotLoadedError, SynthesisError, TimeoutError
from ..schemas.tts import TTSGenerationRequest, TTSModelLoadRequest

logger = logging.getLogger(__name__)
router = APIRouter()
tts_model_state = get_tts_model_state()

def _normalize_voice(voice) -> str:
    """
    Normalize voice parameter to string.
    Accepts both string and dict formats (OpenAI compatibility).
    """
    if isinstance(voice, dict):
        return voice.get("id", voice.get("name", ""))
    return voice

@router.post("/v1/audio/speech")
async def create_speech(request: TTSGenerationRequest, http_request: Request):
    """
    OpenAI-compatible text-to-speech endpoint with streaming support.
    """
    logger.info(f"[TTS] Received request: input_length={len(request.input)}, voice={request.voice}, response_format={request.response_format}, stream_format={request.stream_format}")

    if len(request.input.strip()) == 0:
        logger.warning("[TTS] Rejected request: empty input text")
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    if len(request.input) > 4096:
        logger.warning(f"[TTS] Rejected request: input too long ({len(request.input)} > 4096)")
        raise HTTPException(
            status_code=413,
            detail="Input text exceeds maximum length of 4096 characters."
        )

    voice = _normalize_voice(request.voice)

    supported_formats = ["wav", "pcm", "mp3", "aac", "opus", "flac"]

    if request.response_format not in supported_formats:
        logger.warning(f"[TTS] Rejected request: unsupported format '{request.response_format}'")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{request.response_format}'. Supported formats: {', '.join(supported_formats)}"
        )

    try:
        media_type = {
            "wav": "audio/wav",
            "pcm": "audio/pcm",
            "mp3": "audio/mpeg",
            "aac": "audio/aac",
            "opus": "audio/ogg",
            "flac": "audio/flac",
        }.get(request.response_format, "audio/wav")

        # Determine stream format (default to "audio" if not specified)
        stream_format = request.stream_format or "audio"

        if stream_format == "sse":
            logger.info(f"[TTS] SSE streaming synthesis requested: format={request.response_format}")
            
            stream_generator = await synthesize_streaming(
                text=request.input,
                voice=voice,
                response_format=request.response_format,
                stream_format="sse",
                http_request=http_request
            )
            
            return StreamingResponse(
                stream_generator,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        
        else:
            # Default to audio streaming (chunked transfer encoding)
            # This covers both explicit stream_format="audio" and implicit requests (standard OpenAI client)
            logger.info(f"[TTS] Audio streaming synthesis requested: format={request.response_format}")
            
            stream_generator = await synthesize_streaming(
                text=request.input,
                voice=voice,
                response_format=request.response_format,
                stream_format="audio",
                http_request=http_request
            )
            
            return StreamingResponse(
                stream_generator,
                media_type=media_type,
                headers={"Transfer-Encoding": "chunked"}
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ModelNotLoadedError as e:
        logger.error(f"TTS Synthesis failed: {e}")
        raise HTTPException(status_code=503, detail="TTS model is not loaded.")

    except SynthesisError as e:
        logger.error(f"TTS Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed.")

    except TimeoutError as e:
        logger.error(f"TTS synthesis timeout: {e}")
        raise HTTPException(status_code=408, detail="Speech synthesis request timed out.")

    except Exception as e:
        logger.error(f"Failed to create speech: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create speech.")

@router.post("/v1/models/tts/download")
async def download_tts_model_endpoint(request: TTSModelLoadRequest):
    logger.info(f"Received request to download/load TTS model: {request.model_id} for lang: {request.lang_code}")
    try:
        await tts_model_state.load_model(lang_code=request.lang_code, model_id=request.model_id)
        return {"message": f"TTS Model '{request.model_id}' for lang '{request.lang_code}' loaded successfully."}
    except Exception as e:
        logger.error(f"Failed to process TTS model download request for '{request.model_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load/download TTS model: {str(e)}")
