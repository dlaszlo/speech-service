import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from ..core.config import MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES
from ..core.stt_dependencies import get_model_state
from ..services.stt_service import transcribe_audio
from ..core.exceptions import ModelNotLoadedError, TranscriptionError, TimeoutError

from ..schemas.stt import TranscriptionResponse, STTModelLoadRequest
from ..schemas.system import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()
model_state = get_model_state()

@router.post("/v1/audio/transcriptions", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    temperature: float = Form(0.0)
):
    """
    Transcribes audio using a Whisper model.
    """
    if file.content_type:
        logger.debug(f"Received transcription request with content-type: {file.content_type}")
    
    # Validate that the requested model matches the loaded model
    if model and model_state.model_name and model != model_state.model_name:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not loaded. Currently loaded: '{model_state.model_name}'. Dynamic model switching is not supported via this endpoint."
        )

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB."
        )

    async with model_state.transcription_lock:
        try:
            transcribed_text = await transcribe_audio(
                file_content=file_content,
                language=language,
                prompt=prompt,
                temperature=temperature
            )
            return TranscriptionResponse(text=transcribed_text)
        except ModelNotLoadedError:
            logger.error("Transcription requested but no model is loaded.")
            raise HTTPException(status_code=503, detail="No STT model is currently loaded.")
        except TranscriptionError as e:
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(status_code=500, detail="Internal transcription error.")
        except TimeoutError as e:
            logger.error(f"Transcription timeout: {e}")
            raise HTTPException(status_code=408, detail="Transcription request timed out.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Unexpected server error.")

@router.post("/v1/models/download")
async def download_model_endpoint(request: STTModelLoadRequest):
    logger.info(f"Received request to download/load model: {request.model_name} with compute_type: {request.compute_type}")
    async with model_state.transcription_lock:
        try:
            await model_state.load_model(model_id=request.model_name, compute_type=request.compute_type)
            return {"message": f"Model '{request.model_name}' (compute_type={request.compute_type}) loaded successfully."}
        except Exception as e:
            logger.error(f"Failed to process model download request for '{request.model_name}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to load/download model: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check_endpoint():
    from ..core.tts_dependencies import get_tts_model_state
    tts_model_state = get_tts_model_state()
    
    stt_status = "ok" if model_state.model else "not_loaded"
    tts_status = "ok" if tts_model_state.pipeline else "not_loaded"
    
    if stt_status == "ok" and tts_status == "ok":
        overall_status = "healthy"
    elif stt_status == "ok" or tts_status == "ok":
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
        
    return HealthResponse(
        status=overall_status,
        stt_model=stt_status,
        tts_model=tts_status
    )
