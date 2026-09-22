"""The specialist agents that make up the Model Bias Auditor.

One agent per stage of the audit. Each declares the task types it accepts and returns an
AgentResult, so the orchestrator never needs to know what any stage does internally.
"""

import asyncio
from typing import Any

from app.agents.base import Agent, AgentResult, AgentTask, AgentTaskType
from app.core.config import get_settings
from app.core.logging import get_logger
from app.evaluators.registry import evaluator_registry
from app.probes.base import ProbeCase, ProbeContext, ProbeObservation
from app.probes.registry import probe_registry
from app.reports.generator import ReportGenerator
from app.services.target_adapters import TargetAdapterError, target_adapter_registry

logger = get_logger(__name__)


class ProbeGenerationAgent(Agent):
    """Builds the counterfactual prompt sets for the probes selected in the audit."""

    id = "probe-generation-agent"
    name = "Probe Generation Agent"
    supported_tasks = {AgentTaskType.GENERATE_PROBES}

    async def run(self, task: AgentTask) -> AgentResult:
        probe_ids = task.payload.get("probe_ids") or probe_registry.ids()
        context = ProbeContext(
            audit_id=task.audit_id,
            target_id=task.payload.get("target_id"),
            configuration=task.payload.get("configuration", {}),
        )
        cases: list[dict[str, Any]] = []
        for probe_id in probe_ids:
            case = await probe_registry.get(probe_id).generate(context)
            cases.append(case.model_dump())
        return AgentResult(task_type=task.type, audit_id=task.audit_id, success=True, output={"cases": cases})


class ProbeExecutionAgent(Agent):
    """Sends every variant of every probe to the target and collects the replies."""

    id = "probe-execution-agent"
    name = "Probe Execution Agent"
    supported_tasks = {AgentTaskType.EXECUTE_PROBES}

    async def run(self, task: AgentTask) -> AgentResult:
        target = task.payload.get("target") or {}
        provider = target.get("provider", "mock")
        configuration = {**target.get("configuration", {}), "model_name": target.get("model_name", "mock-model")}
        adapter = target_adapter_registry.get(provider)
        semaphore = asyncio.Semaphore(get_settings().worker_concurrency)

        async def ask(prompt: str) -> tuple[str, str | None]:
            async with semaphore:
                try:
                    return await adapter.complete(prompt, configuration), None
                except TargetAdapterError as exc:
                    logger.warning("target request failed: %s", exc)
                    return "", str(exc)
                except Exception as exc:
                    logger.exception("unexpected target failure")
                    return "", f"{type(exc).__name__}: {exc}"

        observations: list[dict[str, Any]] = []
        for raw_case in task.payload.get("cases", []):
            case = ProbeCase.model_validate(raw_case)
            probe = probe_registry.get(case.probe_id)
            replies = await asyncio.gather(*(ask(variant.prompt) for variant in case.variants))
            responses = {variant.group: reply for variant, (reply, _) in zip(case.variants, replies, strict=True)}
            errors = {
                variant.group: error
                for variant, (_, error) in zip(case.variants, replies, strict=True)
                if error is not None
            }
            observation = await probe.execute(case, responses, errors)
            observations.append(observation.model_dump())

        return AgentResult(task_type=task.type, audit_id=task.audit_id, success=True, output={"observations": observations})


class BiasEvaluationAgent(Agent):
    """Scores each observation by comparing the groups against each other."""

    id = "bias-evaluation-agent"
    name = "Bias Evaluation Agent"
    supported_tasks = {AgentTaskType.EVALUATE_RESPONSES}

    async def run(self, task: AgentTask) -> AgentResult:
        evaluator_id = task.payload.get("evaluator_id") or get_settings().default_evaluator_id
        evaluator = evaluator_registry.get(evaluator_id)
        evaluations: list[dict[str, Any]] = []
        for raw_observation in task.payload.get("observations", []):
            observation = ProbeObservation.model_validate(raw_observation)
            evaluations.append(await evaluator.evaluate(observation))
        return AgentResult(task_type=task.type, audit_id=task.audit_id, success=True, output={"evaluations": evaluations})


class FindingAggregationAgent(Agent):
    """Turns raw evaluations into findings and rolls them up per protected attribute."""

    id = "finding-aggregation-agent"
    name = "Finding Aggregation Agent"
    supported_tasks = {AgentTaskType.AGGREGATE_FINDINGS}

    async def run(self, task: AgentTask) -> AgentResult:
        settings = get_settings()
        evaluations = task.payload.get("evaluations", [])
        findings = [
            evaluation
            for evaluation in evaluations
            if evaluation.get("disparity_score", 0.0) >= settings.disparity_warning_threshold
        ]

        by_attribute: dict[str, dict[str, Any]] = {}
        for evaluation in evaluations:
            attribute = evaluation.get("attribute", "unknown")
            bucket = by_attribute.setdefault(
                attribute,
                {"attribute": attribute, "probes_run": 0, "findings": 0, "max_disparity": 0.0, "severities": []},
            )
            bucket["probes_run"] += 1
            bucket["max_disparity"] = max(bucket["max_disparity"], evaluation.get("disparity_score", 0.0))
            if evaluation.get("disparity_score", 0.0) >= settings.disparity_warning_threshold:
                bucket["findings"] += 1
                bucket["severities"].append(evaluation.get("severity", "info"))

        return AgentResult(
            task_type=task.type,
            audit_id=task.audit_id,
            success=True,
            output={"findings": findings, "attribute_summary": list(by_attribute.values())},
        )


class ReportAgent(Agent):
    """Renders the audit result as JSON, Markdown or HTML."""

    id = "report-agent"
    name = "Report Generation Agent"
    supported_tasks = {AgentTaskType.GENERATE_REPORT}

    async def run(self, task: AgentTask) -> AgentResult:
        generator = ReportGenerator()
        report_format = task.payload.get("format", "json")
        content = generator.build(
            report_format,
            audit_id=task.audit_id,
            audit=task.payload.get("audit", {}),
            findings=task.payload.get("findings", []),
            attribute_summary=task.payload.get("attribute_summary", []),
        )
        return AgentResult(
            task_type=task.type,
            audit_id=task.audit_id,
            success=True,
            output={"format": report_format, "content": content},
        )


class NotificationAgent(Agent):
    """Delivery boundary. Wired to a real channel (email, webhook, chat) in a later milestone."""

    id = "notification-agent"
    name = "Notification Agent"
    supported_tasks = {AgentTaskType.NOTIFY_USER}

    async def run(self, task: AgentTask) -> AgentResult:
        logger.info("audit %s finished with %s findings", task.audit_id, len(task.payload.get("findings", [])))
        return AgentResult(task_type=task.type, audit_id=task.audit_id, success=True, output={"notified": True})


DEFAULT_AGENTS: list[Agent] = [
    ProbeGenerationAgent(),
    ProbeExecutionAgent(),
    BiasEvaluationAgent(),
    FindingAggregationAgent(),
    ReportAgent(),
    NotificationAgent(),
]
