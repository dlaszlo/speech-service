from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for service health check."""
    status: str  # "healthy", "degraded", or "unhealthy"
    stt_model: str  # "ok" or "not_loaded"
    tts_model: str  # "ok" or "not_loaded"
