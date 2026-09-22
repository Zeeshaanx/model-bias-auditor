from fastapi import APIRouter

from app.api.routes import audits, dashboard, health, probes, reports, targets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(targets.router)
api_router.include_router(probes.router)
api_router.include_router(audits.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
