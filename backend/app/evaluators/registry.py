from __future__ import annotations

from app.evaluators.base import BiasEvaluator
from app.evaluators.composite import CompositeDisparityEvaluator
from app.evaluators.disparity import (
    RefusalDisparityEvaluator,
    ResponseEffortEvaluator,
    SentimentDisparityEvaluator,
    StereotypeAssociationEvaluator,
)


class EvaluatorRegistry:
    def __init__(self) -> None:
        evaluators: list[BiasEvaluator] = [
            CompositeDisparityEvaluator(),
            RefusalDisparityEvaluator(),
            SentimentDisparityEvaluator(),
            StereotypeAssociationEvaluator(),
            ResponseEffortEvaluator(),
        ]
        self._evaluators = {evaluator.id: evaluator for evaluator in evaluators}

    def register(self, evaluator: BiasEvaluator) -> None:
        self._evaluators[evaluator.id] = evaluator

    def list(self) -> list[BiasEvaluator]:
        return list(self._evaluators.values())

    def get(self, evaluator_id: str) -> BiasEvaluator:
        if evaluator_id not in self._evaluators:
            raise KeyError(f"Unknown evaluator: {evaluator_id}")
        return self._evaluators[evaluator_id]


evaluator_registry = EvaluatorRegistry()
