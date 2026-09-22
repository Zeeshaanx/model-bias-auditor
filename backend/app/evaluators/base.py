from abc import ABC, abstractmethod
from typing import Any

from app.probes.base import ProbeObservation


class BiasEvaluator(ABC):
    """Scores one probe observation by comparing groups against each other."""

    id: str
    name: str
    description: str
    metric: str

    @abstractmethod
    async def evaluate(self, observation: ProbeObservation) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def coerce(observation: ProbeObservation | dict[str, Any]) -> ProbeObservation:
        if isinstance(observation, ProbeObservation):
            return observation
        return ProbeObservation.model_validate(observation)
