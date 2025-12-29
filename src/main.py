import os
import logging
import traceback
import sys
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from .api.transcription import router as transcription_router
from .api.text_to_speech import router as tts_router
from .api.system import router as system_router
from .core.stt_dependencies import get_model_state
from .core.tts_dependencies import get_tts_model_state

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(threadName)s] %(name)30.30s %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def validate_environment_variables() -> List[str]:
    warnings = []
    
    stt_compute_type = os.getenv('STT_COMPUTE_TYPE', 'auto')
    tts_lang_code = os.getenv('TTS_LANG_CODE', 'a')
    device_override = os.getenv('DEVICE_OVERRIDE')
    
    valid_compute_types = ['auto', 'int8', 'float16', 'int8_float16', 'float32']
    if stt_compute_type not in valid_compute_types:
        warnings.append(f"Invalid STT_COMPUTE_TYPE '{stt_compute_type}'. Valid values: {valid_compute_types}")
    
    if not tts_lang_code or len(tts_lang_code) != 1:
        warnings.append(f"Invalid TTS_LANG_CODE '{tts_lang_code}'. Should be a single character.")
    
    if device_override and device_override not in ['cpu', 'cuda']:
        warnings.append(f"Invalid DEVICE_OVERRIDE '{device_override}'. Valid values: 'cpu', 'cuda'")
    
    return warnings

setup_logging()
logger = logging.getLogger(__name__)

stt_model_state = get_model_state()
tts_model_state = get_tts_model_state()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        validation_warnings = validate_environment_variables()
        for warning in validation_warnings:
            logger.warning(f"Environment validation: {warning}")
        
        # Load STT
        stt_model_name = os.getenv("STT_MODEL_NAME", "Systran/faster-distil-whisper-small.en")
        stt_compute_type = os.getenv("STT_COMPUTE_TYPE", "auto")
        logger.info(f"Startup: Loading STT model: {stt_model_name} ({stt_compute_type})")
        try:
            await stt_model_state.load_model(model_id=stt_model_name, compute_type=stt_compute_type)
            logger.info("STT model loaded.")
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")

        # Load TTS
        tts_lang_code = os.getenv("TTS_LANG_CODE", "a")
        tts_model_name = os.getenv("TTS_MODEL_NAME", "hexgrad/Kokoro-82M")
        logger.info(f"Startup: Loading TTS model '{tts_model_name}' (lang: {tts_lang_code})")
        try:
            await tts_model_state.load_model(lang_code=tts_lang_code, model_id=tts_model_name)
            logger.info("TTS model loaded.")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
        
    except Exception as e:
        logger.error(f"Failed to load models during startup: {e}")
    
    yield
    
    # Shutdown
    try:
        if stt_model_state.model is not None:
            logger.info("Clearing STT model")
            stt_model_state.model = None
            stt_model_state.model_id = None
        
        if tts_model_state.pipeline is not None:
            logger.info("Clearing TTS model")
            tts_model_state.pipeline = None
            tts_model_state.lang_code = None
            tts_model_state.model_id = None
        
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title="Speech Service (STT & TTS)",
    description="Modular API for Speech-to-Text and Text-to-Speech.",
    version="0.4.0",
    lifespan=lifespan,
)

app.include_router(transcription_router, tags=["Speech to Text"])
app.include_router(tts_router, tags=["Text to Speech"])
app.include_router(system_router, tags=["System"])

logger.info("Application setup complete. API is ready.")
