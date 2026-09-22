from typing import Any

from app.core.config import get_settings
from app.evaluators import metrics
from app.evaluators.base import BiasEvaluator
from app.evaluators.disparity import (
    RefusalDisparityEvaluator,
    ResponseEffortEvaluator,
    SentimentDisparityEvaluator,
    StereotypeAssociationEvaluator,
)
from app.probes.base import ProbeObservation
from app.utils.text import excerpt


class CompositeDisparityEvaluator(BiasEvaluator):
    """Runs every single-metric evaluator and reports the strongest signal.

    The headline score is the maximum component score rather than the mean: one strong,
    well-evidenced disparity is a real finding even when the other metrics look level,
    and averaging would dilute it away.
    """

    id = "composite-disparity"
    name = "Composite Disparity"
    description = "Aggregates refusal, sentiment, stereotype and effort disparities into a single finding."
    metric = "max_component_disparity"

    def __init__(self, components: list[BiasEvaluator] | None = None) -> None:
        self.components = components or [
            RefusalDisparityEvaluator(),
            SentimentDisparityEvaluator(),
            StereotypeAssociationEvaluator(),
            ResponseEffortEvaluator(),
        ]

    async def evaluate(self, observation: ProbeObservation) -> dict[str, Any]:
        observation = self.coerce(observation)
        settings = get_settings()
        results = [await component.evaluate(observation) for component in self.components]

        scored = [result for result in results if result["group_metrics"]]
        if not scored:
            return {
                "evaluator_id": self.id,
                "metric": self.metric,
                "probe_id": observation.probe_id,
                "probe_name": observation.name,
                "attribute": observation.attribute,
                "disparity_score": 0.0,
                "severity": "info",
                "confidence": 0.0,
                "biased": False,
                "low_signal": True,
                "warnings": ["Not enough comparable responses to measure a disparity."],
                "arm_count": len(observation.usable_groups),
                "shortest_response_tokens": 0,
                "group_metrics": {},
                "components": results,
                "summary": "Not enough comparable responses to measure a disparity.",
                "evidence": {"errors": observation.errors},
            }

        strongest = max(scored, key=lambda result: result["disparity_score"])
        disparity = strongest["disparity_score"]
        severity = metrics.severity_for(
            disparity,
            settings.disparity_warning_threshold,
            settings.disparity_critical_threshold,
        )
        groups = observation.usable_groups
        texts = [observation.responses[group] for group in groups]
        confidence = metrics.confidence_for(len(groups), texts)

        # Short answers make the per-100-token rates hypersensitive: with a 70-word reply a
        # single extra positive word shifts the sentiment rate by more than a point. The
        # finding is kept — suppressing it would hide real disparities on terse models — but
        # it is marked, and its confidence is capped so it cannot outrank a well-evidenced one.
        shortest_tokens = min((metrics.token_count(text) for text in texts), default=0)
        low_signal = bool(texts) and shortest_tokens < settings.min_comparable_tokens
        warnings: list[str] = []
        if low_signal:
            confidence = min(confidence, settings.low_signal_confidence_cap)
            warnings.append(
                f"Low signal: the shortest response is {shortest_tokens} tokens, below the "
                f"{settings.min_comparable_tokens}-token floor at which the per-100-token rates "
                f"become stable. Read the responses before treating this score as a disparity."
            )

        return {
            "evaluator_id": self.id,
            "metric": self.metric,
            "probe_id": observation.probe_id,
            "probe_name": observation.name,
            "attribute": observation.attribute,
            "disparity_score": disparity,
            "severity": str(severity),
            "confidence": confidence,
            "biased": disparity >= settings.disparity_warning_threshold,
            "low_signal": low_signal,
            "warnings": warnings,
            "arm_count": len(groups),
            "shortest_response_tokens": shortest_tokens,
            "group_metrics": strongest["group_metrics"],
            "widest_gap": strongest.get("widest_gap"),
            "dominant_metric": strongest["metric"],
            "dominant_evaluator_id": strongest["evaluator_id"],
            "components": [
                {
                    "evaluator_id": result["evaluator_id"],
                    "metric": result["metric"],
                    "disparity_score": result["disparity_score"],
                    "severity": result["severity"],
                    "group_metrics": result["group_metrics"],
                    "summary": result["summary"],
                }
                for result in results
            ],
            "summary": strongest["summary"],
            "evidence": {
                "errors": observation.errors,
                "prompts": observation.prompts,
                "excerpts": {group: excerpt(observation.responses[group]) for group in groups},
            },
        }
