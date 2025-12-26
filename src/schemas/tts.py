from pydantic import BaseModel

class TTSGenerationRequest(BaseModel):
    """Request model for generating speech from text."""
    model: str # For OpenAI compatibility (e.g., 'kokoro')
    input: str
    voice: str # e.g., "af_heart"

class TTSModelLoadRequest(BaseModel):
    """Request model for loading a specific TTS model/language."""
    lang_code: str # e.g., "a" for American English
    model_id: str = "onnx-community/Kokoro-82M-v1.0-ONNX"
    compute_type: str = "auto"
