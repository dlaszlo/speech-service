import logging
import asyncio
import os
import torch
from faster_whisper import WhisperModel
from .config import MODEL_LOAD_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

class STTModelState:
    def __init__(self):
        self.model = None
        self.model_name = None
        self.compute_type = "float16"
        self.device = "cpu"
        self.transcription_lock = asyncio.Lock()
        self.model_load_lock = asyncio.Lock()

    async def load_model(self, model_id: str, compute_type: str = "auto"):
        async with self.model_load_lock:
            if self.model and self.model_name == model_id and self.compute_type == compute_type:
                return

            logger.info(f"Loading Faster-Whisper model: {model_id} (compute_type: {compute_type})")
            
            device_override = os.getenv("DEVICE_OVERRIDE")
            if device_override:
                self.device = device_override
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
            


            try:
                self.model = await asyncio.wait_for(
                    asyncio.to_thread(
                        WhisperModel,
                        model_size_or_path=model_id,
                        device=self.device,
                        compute_type=compute_type
                    ),
                    timeout=MODEL_LOAD_TIMEOUT_SECONDS
                )
                
                self.model_name = model_id
                self.compute_type = compute_type
                logger.info(f"Loaded Faster-Whisper model '{model_id}' on {self.device}.")
                
            except Exception as e:
                logger.error(f"Failed to load model '{model_id}': {e}", exc_info=True)
                self.model = None
                self.model_name = None
                raise

model_state = STTModelState()

def get_model_state():
    return model_state
