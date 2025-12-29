import logging
import asyncio
import os
import torch
from .config import MODEL_LOAD_TIMEOUT_SECONDS

try:
    from kokoro import KPipeline
except ImportError:
    KPipeline = None

logger = logging.getLogger(__name__)

class TTSModelState:
    def __init__(self):
        self.pipeline = None
        self.lang_code = None
        self.model_id = None
        self.model_load_lock = asyncio.Lock()

        if KPipeline is None:
            logger.warning("Kokoro library not installed. TTS disabled.")

    async def load_model(self, lang_code: str, model_id: str = "hexgrad/Kokoro-82M"):
        async with self.model_load_lock:
            if self.pipeline and self.lang_code == lang_code and self.model_id == model_id:
                return

            if KPipeline is None:
                raise ImportError("Kokoro library is not installed.")

            device_override = os.getenv("DEVICE_OVERRIDE")
            if device_override:
                device = device_override
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

            logger.info(f"Loading Kokoro TTS: lang={lang_code}, model={model_id}, device={device}")

            try:
                self.pipeline = await asyncio.wait_for(
                    asyncio.to_thread(KPipeline, lang_code=lang_code, repo_id=model_id, device=device),
                    timeout=MODEL_LOAD_TIMEOUT_SECONDS
                )
                self.lang_code = lang_code
                self.model_id = model_id
                logger.info(f"Loaded Kokoro TTS pipeline.")
            except Exception as e:
                error_msg = str(e)
                if "'vocab'" in error_msg:
                    logger.error("Kokoro config error (missing vocab). Known ONNX issue.")
                else:
                    logger.error(f"Failed to load Kokoro TTS: {e}", exc_info=True)
                
                self.pipeline = None
                self.lang_code = None
                self.model_id = None
                raise

tts_model_state = TTSModelState()

def get_tts_model_state():
    return tts_model_state