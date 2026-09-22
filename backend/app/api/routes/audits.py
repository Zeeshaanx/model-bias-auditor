from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.audit import AuditCreate, AuditRead, AuditRunResponse, AuditUpdate
from app.schemas.finding import FindingRead, ProbeResultRead
from app.services import audit as audit_service
from app.services import target as target_service

router = APIRouter(prefix="/audits", tags=["audits"])


async def _load(session: AsyncSession, audit_id: str):
    audit = await audit_service.get_audit(session, audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    return audit


@router.post("", response_model=AuditRead, status_code=status.HTTP_201_CREATED)
async def create_audit(payload: AuditCreate, session: AsyncSession = Depends(get_session)) -> AuditRead:
    if await target_service.get_target(session, payload.target_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target not found")
    return AuditRead.model_validate(await audit_service.create_audit(session, payload))


@router.get("", response_model=list[AuditRead])
async def list_audits(session: AsyncSession = Depends(get_session)) -> list[AuditRead]:
    return [AuditRead.model_validate(item) for item in await audit_service.list_audits(session)]


@router.get("/{audit_id}", response_model=AuditRead)
async def get_audit(audit_id: str, session: AsyncSession = Depends(get_session)) -> AuditRead:
    return AuditRead.model_validate(await _load(session, audit_id))


@router.patch("/{audit_id}", response_model=AuditRead)
async def update_audit(audit_id: str, payload: AuditUpdate, session: AsyncSession = Depends(get_session)) -> AuditRead:
    audit = await _load(session, audit_id)
    return AuditRead.model_validate(await audit_service.update_audit(session, audit, payload))


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit(audit_id: str, session: AsyncSession = Depends(get_session)) -> None:
    await audit_service.delete_audit(session, await _load(session, audit_id))


@router.post("/{audit_id}/run", response_model=AuditRunResponse)
async def run_audit(audit_id: str, session: AsyncSession = Depends(get_session)) -> AuditRunResponse:
    audit = await _load(session, audit_id)
    target = await target_service.get_target(session, audit.target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target not found")
    try:
        summary = await audit_service.run_audit(session, audit, target)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return AuditRunResponse(**summary)


@router.get("/{audit_id}/findings", response_model=list[FindingRead])
async def list_findings(audit_id: str, session: AsyncSession = Depends(get_session)) -> list[FindingRead]:
    await _load(session, audit_id)
    return [FindingRead.model_validate(item) for item in await audit_service.list_findings(session, audit_id)]


@router.get("/{audit_id}/results", response_model=list[ProbeResultRead])
async def list_probe_results(audit_id: str, session: AsyncSession = Depends(get_session)) -> list[ProbeResultRead]:
    await _load(session, audit_id)
    return [ProbeResultRead.model_validate(item) for item in await audit_service.list_probe_results(session, audit_id)]
