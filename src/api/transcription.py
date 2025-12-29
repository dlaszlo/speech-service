import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from ..core.config import MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES
from ..core.stt_dependencies import get_model_state
from ..services.stt_service import transcribe
from ..core.exceptions import ModelNotLoadedError, TranscriptionError, TimeoutError
from ..core.error_handler import InvalidModelError

from ..schemas.stt import TranscriptionResponse, STTModelLoadRequest

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
    logger.info(f"[STT] Received transcription request: filename={file.filename}, content_type={file.content_type}, model={model}, language={language}, temperature={temperature}")

    if file.content_type:
        logger.debug(f"Received transcription request with content-type: {file.content_type}")

    # Validate that the requested model matches the loaded model
    # Validate that the requested model matches the loaded model
    if model and model_state.model_id and model != model_state.model_id:
        logger.warning(f"[STT] Rejected request: model mismatch (requested='{model}', loaded='{model_state.model_id}')")
        raise InvalidModelError(model)

    file_content = await file.read()
    logger.info(f"[STT] Read file content, size={len(file_content)} bytes")

    if len(file_content) > MAX_FILE_SIZE_BYTES:
        logger.warning(f"[STT] Rejected request: file too large ({len(file_content)} > {MAX_FILE_SIZE_BYTES})")
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB."
        )

    logger.info("[STT] Starting transcription")
    transcribed_text = await transcribe(
        file_content=file_content,
        language=language,
        prompt=prompt,
        temperature=temperature
    )
    logger.info(f"[STT] Transcription completed, result_length={len(transcribed_text)}")
    return TranscriptionResponse(text=transcribed_text)

@router.post("/v1/models/stt/download")
async def download_model_endpoint(request: STTModelLoadRequest):
    logger.info(f"Received request to download/load model: {request.model_id} with compute_type: {request.compute_type}")
    try:
        await model_state.load_model(model_id=request.model_id, compute_type=request.compute_type)
        return {"message": f"Model '{request.model_id}' (compute_type={request.compute_type}) loaded successfully."}
    except Exception as e:
        logger.error(f"Failed to process model download request for '{request.model_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load/download model: {str(e)}")
