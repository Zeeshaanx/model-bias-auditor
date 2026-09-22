from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.report import ReportCreate, ReportRead
from app.services import audit as audit_service
from app.services import report as report_service

router = APIRouter(prefix="/reports", tags=["reports"])

_MEDIA_TYPES = {"json": "application/json", "markdown": "text/markdown; charset=utf-8", "html": "text/html; charset=utf-8"}


@router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(payload: ReportCreate, session: AsyncSession = Depends(get_session)) -> ReportRead:
    audit = await audit_service.get_audit(session, payload.audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
    report = await report_service.generate_report(session, audit, str(payload.format))
    return ReportRead.model_validate(report)


@router.get("", response_model=list[ReportRead])
async def list_reports(audit_id: str | None = None, session: AsyncSession = Depends(get_session)) -> list[ReportRead]:
    return [ReportRead.model_validate(item) for item in await report_service.list_reports(session, audit_id)]


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(report_id: str, session: AsyncSession = Depends(get_session)) -> ReportRead:
    report = await report_service.get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ReportRead.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(report_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    report = await report_service.get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    extension = {"json": "json", "markdown": "md", "html": "html"}.get(report.format, "txt")
    return Response(
        content=report.content,
        media_type=_MEDIA_TYPES.get(report.format, "text/plain; charset=utf-8"),
        headers={"Content-Disposition": f'attachment; filename="bias-audit-{report.audit_id}.{extension}"'},
    )
