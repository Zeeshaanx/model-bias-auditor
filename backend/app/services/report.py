from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentTask, AgentTaskType
from app.agents.orchestrator import agent_orchestrator
from app.models.audit import Audit
from app.models.report import Report
from app.models.target import Target
from app.services.audit import list_findings


async def generate_report(session: AsyncSession, audit: Audit, report_format: str) -> Report:
    findings = await list_findings(session, audit.id)
    target = await session.get(Target, audit.target_id)

    attribute_summary: dict[str, dict] = {}
    for finding in findings:
        bucket = attribute_summary.setdefault(
            finding.attribute,
            {"attribute": finding.attribute, "probes_run": 0, "findings": 0, "max_disparity": 0.0},
        )
        bucket["probes_run"] += 1
        bucket["findings"] += 1
        bucket["max_disparity"] = max(bucket["max_disparity"], finding.disparity_score)

    result = await agent_orchestrator.dispatch(
        AgentTask(
            type=AgentTaskType.GENERATE_REPORT,
            audit_id=audit.id,
            payload={
                "format": report_format,
                "audit": {
                    "name": audit.name,
                    "evaluator_id": audit.evaluator_id,
                    "status": audit.status,
                    "target_name": target.name if target else "unknown",
                    "provider": target.provider if target else "unknown",
                    "model_name": target.model_name if target else "unknown",
                },
                "findings": [
                    {
                        "probe_id": finding.probe_id,
                        "probe_name": finding.probe_name or finding.probe_id,
                        "dominant_metric": finding.metric,
                        "attribute": finding.attribute,
                        "evaluator_id": finding.evaluator_id,
                        "severity": finding.severity,
                        "disparity_score": finding.disparity_score,
                        "confidence": finding.confidence,
                        "arm_count": finding.arm_count,
                        "warnings": (
                            [
                                "Low signal: the responses were short enough that wording alone "
                                "can move this score. Read the stored responses before quoting it."
                            ]
                            if finding.low_signal
                            else []
                        ),
                        "summary": finding.summary,
                        "group_metrics": finding.metrics,
                        "evidence": finding.evidence,
                    }
                    for finding in findings
                ],
                "attribute_summary": list(attribute_summary.values()),
            },
        )
    )

    report = Report(audit_id=audit.id, format=report_format, content=result.output["content"])
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def list_reports(session: AsyncSession, audit_id: str | None = None) -> list[Report]:
    statement = select(Report).order_by(Report.created_at.desc())
    if audit_id:
        statement = statement.where(Report.audit_id == audit_id)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_report(session: AsyncSession, report_id: str) -> Report | None:
    return await session.get(Report, report_id)
