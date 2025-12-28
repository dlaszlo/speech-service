import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..services.tts_service import synthesize
from ..core.tts_dependencies import get_tts_model_state
from ..core.exceptions import ModelNotLoadedError, SynthesisError, TimeoutError
from ..schemas.tts import TTSGenerationRequest, TTSModelLoadRequest

logger = logging.getLogger(__name__)
router = APIRouter()
tts_model_state = get_tts_model_state()

@router.post("/v1/audio/speech")
async def create_speech(request: TTSGenerationRequest):
    if len(request.input.strip()) == 0:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    if len(request.input) > 10000:
        raise HTTPException(
            status_code=413,
            detail="Input text exceeds maximum length of 10000 characters."
        )

    # Validate that the requested model matches the loaded model
    if request.model and tts_model_state.model_id and request.model != tts_model_state.model_id:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' is not loaded. Currently loaded: '{tts_model_state.model_id}'. Dynamic model switching is not supported via this endpoint."
        )

    async with tts_model_state.synthesis_lock:
        try:
            wav_bytes = await synthesize(text=request.input, voice=request.voice)
            return StreamingResponse(iter([wav_bytes]), media_type="audio/wav")
        
        except ModelNotLoadedError as e:
            logger.error(f"TTS Synthesis failed: {e}")
            raise HTTPException(status_code=503, detail="TTS model is not loaded.")
        except SynthesisError as e:
            logger.error(f"TTS Synthesis failed: {e}")
            raise HTTPException(status_code=500, detail="Speech synthesis failed.")
        except TimeoutError as e:
            logger.error(f"TTS synthesis timeout: {e}")
            raise HTTPException(status_code=408, detail="Speech synthesis request timed out.")
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to create speech: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create speech.")

@router.post("/v1/models/tts/download")
async def download_tts_model_endpoint(request: TTSModelLoadRequest):
    logger.info(f"Received request to download/load TTS model: {request.model_id} for lang: {request.lang_code}")
    async with tts_model_state.synthesis_lock:
        try:
            await tts_model_state.load_model(lang_code=request.lang_code, model_id=request.model_id)
            return {"message": f"TTS Model '{request.model_id}' for lang '{request.lang_code}' loaded successfully."}
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to process TTS model download request for '{request.model_id}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to load/download TTS model: {str(e)}")