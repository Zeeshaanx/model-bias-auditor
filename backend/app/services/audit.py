"""The audit workflow.

The service owns ordering and persistence. Every unit of actual work is delegated to the
orchestrator, so this file stays readable as a description of the pipeline:

    generate probes -> execute against target -> evaluate -> aggregate -> notify
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentTask, AgentTaskType
from app.agents.orchestrator import agent_orchestrator
from app.core.logging import get_logger
from app.models.audit import Audit
from app.models.enums import AuditStatus
from app.models.finding import Finding
from app.models.probe_result import ProbeResult
from app.models.target import Target
from app.probes.registry import probe_registry
from app.schemas.audit import AuditCreate, AuditUpdate
from app.services import activity

logger = get_logger(__name__)


async def create_audit(session: AsyncSession, payload: AuditCreate) -> Audit:
    audit = Audit(
        name=payload.name,
        description=payload.description,
        target_id=payload.target_id,
        probe_ids=payload.probe_ids or probe_registry.ids(),
        evaluator_id=payload.evaluator_id,
        configuration=payload.configuration,
        status=str(AuditStatus.PENDING),
    )
    session.add(audit)
    await session.flush()
    await activity.record(session, "audit", audit.id, "created", {"probes": len(audit.probe_ids)})
    await session.commit()
    await session.refresh(audit)
    return audit


async def list_audits(session: AsyncSession) -> list[Audit]:
    result = await session.execute(select(Audit).order_by(Audit.created_at.desc()))
    return list(result.scalars().all())


async def get_audit(session: AsyncSession, audit_id: str) -> Audit | None:
    return await session.get(Audit, audit_id)


async def update_audit(session: AsyncSession, audit: Audit, payload: AuditUpdate) -> Audit:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(audit, field, value)
    await session.commit()
    await session.refresh(audit)
    return audit


async def delete_audit(session: AsyncSession, audit: Audit) -> None:
    await session.delete(audit)
    await session.commit()


async def list_findings(session: AsyncSession, audit_id: str) -> list[Finding]:
    result = await session.execute(
        select(Finding).where(Finding.audit_id == audit_id).order_by(Finding.disparity_score.desc())
    )
    return list(result.scalars().all())


async def list_probe_results(session: AsyncSession, audit_id: str) -> list[ProbeResult]:
    result = await session.execute(select(ProbeResult).where(ProbeResult.audit_id == audit_id))
    return list(result.scalars().all())


async def run_audit(session: AsyncSession, audit: Audit, target: Target) -> dict[str, Any]:
    audit.status = str(AuditStatus.RUNNING)
    audit.started_at = datetime.now(UTC)
    audit.error = None
    await session.commit()

    try:
        generated = await agent_orchestrator.dispatch(
            AgentTask(
                type=AgentTaskType.GENERATE_PROBES,
                audit_id=audit.id,
                payload={
                    "probe_ids": audit.probe_ids,
                    "target_id": target.id,
                    "configuration": audit.configuration,
                },
            )
        )

        executed = await agent_orchestrator.dispatch(
            AgentTask(
                type=AgentTaskType.EXECUTE_PROBES,
                audit_id=audit.id,
                payload={
                    "cases": generated.output["cases"],
                    "target": {
                        "provider": target.provider,
                        "model_name": target.model_name,
                        "configuration": target.configuration,
                    },
                },
            )
        )

        evaluated = await agent_orchestrator.dispatch(
            AgentTask(
                type=AgentTaskType.EVALUATE_RESPONSES,
                audit_id=audit.id,
                payload={
                    "observations": executed.output["observations"],
                    "evaluator_id": audit.evaluator_id,
                },
            )
        )

        aggregated = await agent_orchestrator.dispatch(
            AgentTask(
                type=AgentTaskType.AGGREGATE_FINDINGS,
                audit_id=audit.id,
                payload={"evaluations": evaluated.output["evaluations"]},
            )
        )

        await _persist(session, audit, executed.output["observations"], aggregated.output["findings"])

        await agent_orchestrator.dispatch(
            AgentTask(
                type=AgentTaskType.NOTIFY_USER,
                audit_id=audit.id,
                payload={"findings": aggregated.output["findings"]},
            )
        )

        audit.status = str(AuditStatus.COMPLETED)
        audit.completed_at = datetime.now(UTC)
        await activity.record(session, "audit", audit.id, "completed", {"findings": len(aggregated.output["findings"])})
        await session.commit()

        findings = aggregated.output["findings"]
        return {
            "audit_id": audit.id,
            "status": audit.status,
            "probes_run": len(evaluated.output["evaluations"]),
            "findings": len(findings),
            "highest_disparity": max((finding["disparity_score"] for finding in findings), default=0.0),
            "attribute_summary": aggregated.output["attribute_summary"],
        }

    except Exception as exc:
        logger.exception("audit %s failed", audit.id)
        audit.status = str(AuditStatus.FAILED)
        audit.completed_at = datetime.now(UTC)
        audit.error = f"{type(exc).__name__}: {exc}"
        await session.commit()
        raise


async def _persist(
    session: AsyncSession,
    audit: Audit,
    observations: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> None:
    for stale in await list_probe_results(session, audit.id):
        await session.delete(stale)
    for stale_finding in await list_findings(session, audit.id):
        await session.delete(stale_finding)
    await session.flush()

    for observation in observations:
        session.add(
            ProbeResult(
                audit_id=audit.id,
                probe_id=observation["probe_id"],
                attribute=observation["attribute"],
                prompts=observation["prompts"],
                responses=observation["responses"],
                errors=observation["errors"],
            )
        )

    for finding in findings:
        session.add(
            Finding(
                audit_id=audit.id,
                probe_id=finding["probe_id"],
                probe_name=finding.get("probe_name", finding["probe_id"]),
                attribute=finding["attribute"],
                evaluator_id=finding["evaluator_id"],
                metric=finding.get("dominant_metric", finding.get("metric", "")),
                severity=finding["severity"],
                disparity_score=finding["disparity_score"],
                confidence=finding["confidence"],
                arm_count=int(finding.get("arm_count", 0)),
                low_signal=bool(finding.get("low_signal", False)),
                summary=finding.get("summary", ""),
                metrics=finding.get("group_metrics", {}),
                evidence=finding.get("evidence", {}),
            )
        )
    await session.flush()
