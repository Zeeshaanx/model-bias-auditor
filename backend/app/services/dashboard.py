from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit
from app.models.enums import AuditStatus, Severity
from app.models.finding import Finding
from app.models.target import Target


async def _scalar(session: AsyncSession, statement) -> int:
    result = await session.execute(statement)
    return int(result.scalar() or 0)


async def build_metrics(session: AsyncSession) -> dict[str, Any]:
    targets = await _scalar(session, select(func.count()).select_from(Target))
    audits = await _scalar(session, select(func.count()).select_from(Audit))
    running = await _scalar(
        session, select(func.count()).select_from(Audit).where(Audit.status == str(AuditStatus.RUNNING))
    )
    findings = await _scalar(session, select(func.count()).select_from(Finding))
    critical = await _scalar(
        session, select(func.count()).select_from(Finding).where(Finding.severity == str(Severity.CRITICAL))
    )

    low_signal = await _scalar(
        session, select(func.count()).select_from(Finding).where(Finding.low_signal.is_(True))
    )

    highest = await session.execute(select(func.max(Finding.disparity_score)))
    highest_disparity = float(highest.scalar() or 0.0)

    # The probe count travels with the max: an attribute with eight probes has eight draws
    # at the maximum and will tend to top the chart regardless of the model's behaviour.
    # Showing the count alongside the bar is what stops it being read as a bias ranking.
    by_attribute = await session.execute(
        select(
            Finding.attribute,
            func.count(),
            func.max(Finding.disparity_score),
            func.count(func.distinct(Finding.probe_id)),
        ).group_by(Finding.attribute)
    )
    by_severity = await session.execute(select(Finding.severity, func.count()).group_by(Finding.severity))

    recent = await session.execute(select(Audit).order_by(Audit.created_at.desc()).limit(5))

    return {
        "targets": targets,
        "audits": audits,
        "audits_running": running,
        "findings": findings,
        "critical_findings": critical,
        "highest_disparity": round(highest_disparity, 4),
        "findings_by_attribute": [
            {
                "attribute": attribute,
                "findings": count,
                "max_disparity": round(float(maximum or 0.0), 4),
                "probes": probes,
            }
            for attribute, count, maximum, probes in by_attribute.all()
        ],
        "low_signal_findings": low_signal,
        "findings_by_severity": {severity: count for severity, count in by_severity.all()},
        "recent_audits": [
            {"id": audit.id, "name": audit.name, "status": audit.status, "created_at": audit.created_at.isoformat()}
            for audit in recent.scalars().all()
        ],
    }
