from pydantic import BaseModel

class TranscriptionResponse(BaseModel):
    """Response model for audio transcription."""
    text: str

class STTModelLoadRequest(BaseModel):
    """Request model for loading a specific STT model."""
    model_id: str
    compute_type: str = "auto"
