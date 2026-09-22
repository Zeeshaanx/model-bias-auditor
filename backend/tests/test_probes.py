import pytest

from app.models.enums import Jurisdiction, ProtectedAttribute
from app.probes.base import ProbeContext
from app.probes.registry import probe_registry

VALID_JURISDICTIONS = {member.value for member in Jurisdiction}
VALID_ATTRIBUTES = {member.value for member in ProtectedAttribute}


async def test_every_probe_has_at_least_two_arms():
    for probe in probe_registry.list():
        case = await probe.generate(ProbeContext())
        assert len(case.variants) >= 2, f"{probe.id} needs at least two groups to be comparable"


async def test_variants_differ_only_by_substituted_token():
    probe = probe_registry.get("us-hiring-summary-race-male")
    case = await probe.generate(ProbeContext())
    prompts = {variant.group: variant.prompt for variant in case.variants}
    assert len(set(prompts.values())) == len(prompts), "each arm must produce a distinct prompt"
    for variant in case.variants:
        rebuilt = case.template.format(**variant.substitutions)
        assert rebuilt == variant.prompt


async def test_arms_are_identical_apart_from_the_substituted_token():
    """The counterfactual claim only holds if the arms share every other token."""
    for probe in probe_registry.list():
        case = await probe.generate(ProbeContext())
        for variant in case.variants:
            placeholders = set(variant.substitutions)
            stripped = case.template
            for key in placeholders:
                stripped = stripped.replace("{" + key + "}", "")
            remainder = variant.prompt
            for value in variant.substitutions.values():
                remainder = remainder.replace(value, "", 1)
            assert remainder == stripped, f"{probe.id}:{variant.group} diverges outside its substitutions"


async def test_every_probe_declares_a_valid_jurisdiction():
    for probe in probe_registry.list():
        assert probe.jurisdiction in VALID_JURISDICTIONS, f"{probe.id} has no valid jurisdiction"


async def test_every_probe_declares_a_valid_attribute():
    for probe in probe_registry.list():
        assert probe.attribute in VALID_ATTRIBUTES, f"{probe.id} has an unknown attribute"


async def test_every_probe_records_the_provenance_of_its_groups():
    """A probe whose group markers have no stated provenance has no external validity."""
    for probe in probe_registry.list():
        assert probe.source.strip(), f"{probe.id} does not say where its group markers came from"
        assert probe.legal_basis.strip(), f"{probe.id} does not state a legal basis"


async def test_jurisdiction_filter_includes_cross_jurisdiction_probes():
    us = probe_registry.by_jurisdiction(Jurisdiction.US)
    ids = {probe.id for probe in us}
    assert "us-hiring-summary-race-male" in ids
    assert "leadership-potential-age" in ids, "cross-jurisdiction probes travel with every filter"
    assert "eu-de-hiring-summary-origin" not in ids, "German names do not belong in a US audit"


async def test_both_jurisdictions_are_represented():
    by_jurisdiction = {probe.jurisdiction for probe in probe_registry.list()}
    assert {Jurisdiction.US, Jurisdiction.EU, Jurisdiction.CROSS} <= by_jurisdiction


async def test_unknown_probe_raises():
    with pytest.raises(KeyError):
        probe_registry.get("does-not-exist")
