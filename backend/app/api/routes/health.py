from fastapi import APIRouter

from app.core.config import get_settings
from app.evaluators.registry import evaluator_registry
from app.probes.registry import probe_registry
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        probes=len(probe_registry.list()),
        evaluators=len(evaluator_registry.list()),
    )
