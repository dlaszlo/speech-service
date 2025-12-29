from pydantic import BaseModel, field_validator
from typing import Literal, Union, Optional

class TTSGenerationRequest(BaseModel):
    """Request model for generating speech from text."""
    model: str
    input: str
    voice: Union[str, dict]

    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"
    speed: float = 1.0
    stream_format: Optional[Literal["audio", "sse"]] = None
    instructions: Optional[str] = None

    @field_validator('input')
    @classmethod
    def validate_input_length(cls, v: str) -> str:
        if len(v) > 4096:
            raise ValueError('Input text exceeds maximum length of 4096 characters.')
        if len(v.strip()) == 0:
            raise ValueError('Input text cannot be empty.')
        return v

class TTSModelLoadRequest(BaseModel):
    """Request model for loading a specific TTS model/language."""
    lang_code: str # e.g., "a" for American English
    model_id: str = "hexgrad/Kokoro-82M"
