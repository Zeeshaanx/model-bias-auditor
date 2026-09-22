from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ProbeContext(BaseModel):
    """Everything a probe needs to build its test case."""

    audit_id: str | None = None
    target_id: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class ProbeVariant(BaseModel):
    """One arm of a counterfactual test: the same request, one attribute changed."""

    variant_id: str
    group: str
    prompt: str
    substitutions: dict[str, str] = Field(default_factory=dict)


class ProbeCase(BaseModel):
    """A group of prompts that differ only in the protected attribute under test."""

    probe_id: str
    name: str
    attribute: str
    template: str
    variants: list[ProbeVariant]

    @property
    def groups(self) -> list[str]:
        return [variant.group for variant in self.variants]


class ProbeObservation(BaseModel):
    """What actually came back from the target, keyed by group."""

    probe_id: str
    name: str
    attribute: str
    prompts: dict[str, str] = Field(default_factory=dict)
    responses: dict[str, str] = Field(default_factory=dict)
    errors: dict[str, str] = Field(default_factory=dict)

    @property
    def usable_groups(self) -> list[str]:
        return [group for group, text in self.responses.items() if text and text.strip()]


class BiasProbe(ABC):
    """Interface every bias probe implements.

    A probe is deliberately shaped like the attack plugin in the red teaming platform
    (generate -> execute -> evaluate), with one structural difference: a probe never
    produces a single prompt. It produces a *set* of prompts that are identical apart
    from one protected attribute, because bias is only observable by comparison.
    """

    id: str
    name: str
    description: str
    attribute: str

    #: Where this probe's names, situations and legal framing are valid. See
    #: ``app.models.enums.Jurisdiction``. Probes are not portable between
    #: jurisdictions, so this is part of a probe's identity, not metadata.
    jurisdiction: str = "cross"

    #: Provenance of the group markers used in this probe. Where the names come
    #: from a published correspondence study, that study is cited here; where they
    #: were constructed, this says so. A probe whose names have no provenance is a
    #: probe whose findings have no external validity.
    source: str = "Constructed for this project; no published name set."

    #: The statute or instrument that makes a disparity on this attribute legally
    #: relevant in this jurisdiction. Documentation, not enforcement.
    legal_basis: str = ""

    @abstractmethod
    async def generate(self, context: ProbeContext) -> ProbeCase:
        """Build the counterfactual prompt set."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, case: ProbeCase, responses: dict[str, str], errors: dict[str, str] | None = None) -> ProbeObservation:
        """Attach the target's responses to the case."""
        raise NotImplementedError

    @abstractmethod
    async def evaluate(self, observation: ProbeObservation) -> dict[str, Any]:
        """Cheap self-check. Deep scoring is the evaluator layer's job."""
        raise NotImplementedError
