from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import agent_orchestrator
from app.db.session import get_session
from app.schemas.dashboard import DashboardMetrics
from app.services.dashboard import build_metrics

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardMetrics)
async def dashboard(session: AsyncSession = Depends(get_session)) -> DashboardMetrics:
    return DashboardMetrics(**await build_metrics(session))


@router.get("/agents")
async def list_agents() -> list[dict]:
    return agent_orchestrator.describe()
