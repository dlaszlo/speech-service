import logging
from fastapi import APIRouter

from ..core.stt_dependencies import get_model_state
from ..core.tts_dependencies import get_tts_model_state
from ..schemas.system import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()
model_state = get_model_state()

@router.get("/health", response_model=HealthResponse)
async def health_check_endpoint():
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
