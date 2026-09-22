"""The generic counterfactual probe: one template, one placeholder set, many arms."""

from __future__ import annotations

from typing import Any

from app.models.enums import Jurisdiction
from app.probes.base import BiasProbe, ProbeCase, ProbeContext, ProbeObservation, ProbeVariant


class CounterfactualProbe(BiasProbe):
    """One request template plus a set of group substitutions.

    Every arm is generated from the same template, so the task, the length and the
    wording are held identical and any difference in the answers is attributable to
    the substituted token.
    """

    def __init__(
        self,
        probe_id: str,
        name: str,
        description: str,
        attribute: str,
        template: str,
        groups: dict[str, dict[str, str]],
        *,
        jurisdiction: str = Jurisdiction.CROSS,
        source: str = "Constructed for this project; no published name set.",
        legal_basis: str = "",
    ) -> None:
        self.id = probe_id
        self.name = name
        self.description = description
        self.attribute = attribute
        self.template = template
        self.groups = groups
        self.jurisdiction = jurisdiction
        self.source = source
        self.legal_basis = legal_basis

    async def generate(self, context: ProbeContext) -> ProbeCase:
        variants = [
            ProbeVariant(
                variant_id=f"{self.id}:{group}",
                group=group,
                prompt=self.template.format(**substitutions),
                substitutions=substitutions,
            )
            for group, substitutions in self.groups.items()
        ]
        return ProbeCase(
            probe_id=self.id,
            name=self.name,
            attribute=self.attribute,
            template=self.template,
            variants=variants,
        )

    async def execute(
        self,
        case: ProbeCase,
        responses: dict[str, str],
        errors: dict[str, str] | None = None,
    ) -> ProbeObservation:
        return ProbeObservation(
            probe_id=case.probe_id,
            name=case.name,
            attribute=case.attribute,
            prompts={variant.group: variant.prompt for variant in case.variants},
            responses={group: responses.get(group, "") for group in case.groups},
            errors=errors or {},
        )

    async def evaluate(self, observation: ProbeObservation) -> dict[str, Any]:
        usable = observation.usable_groups
        distinct = len({observation.responses[group].strip() for group in usable})
        return {
            "probe_id": self.id,
            "attribute": self.attribute,
            "jurisdiction": self.jurisdiction,
            "groups_expected": len(self.groups),
            "groups_answered": len(usable),
            "comparable": len(usable) >= 2,
            "identical_responses": len(usable) >= 2 and distinct == 1,
            "errors": observation.errors,
        }
