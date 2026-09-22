"""Calibration tests: do the disparity scores respond to a disparity that is really there?

Every other test in this suite checks that the code runs. These check that the
*measurement* behaves, by planting known ground truth in the mock target and asserting the
result. Two claims are under test:

    fair mode    -> zero findings across the whole suite. The tool does not cry wolf.
    biased mode  -> a finding on exactly the probes carrying the planted marker, naming the
                    planted group. The tool is not blind.

What passing these proves: the evaluators react correctly to a signal planted in synthetic
text. What it does not prove: that the metrics are meaningful on real model output. That
needs a real target and human review of the evidence.
"""

import pytest

from app.core.config import get_settings
from app.evaluators.registry import evaluator_registry
from app.probes.base import ProbeContext
from app.probes.registry import probe_registry
from app.services.target_adapters import (
    _DEFAULT_PLANTED_MARKERS,
    TargetAdapterError,
    target_adapter_registry,
)


async def audit_all(mode: str) -> dict[str, dict]:
    """Run every registered probe against the mock in one mode. Returns {probe_id: evaluation}."""
    adapter = target_adapter_registry.get("mock")
    evaluator = evaluator_registry.get("composite-disparity")
    configuration = {"model_name": "mock-model", "mode": mode}

    results = {}
    for probe in probe_registry.list():
        case = await probe.generate(ProbeContext())
        responses = {
            variant.group: await adapter.complete(variant.prompt, configuration)
            for variant in case.variants
        }
        results[probe.id] = await evaluator.evaluate(await probe.execute(case, responses))
    return results


def planted_groups(probe_id: str) -> set[str]:
    """Which arms of this probe contain a planted marker."""
    probe = probe_registry.get(probe_id)
    return {
        group
        for group, substitutions in probe.groups.items()
        if any(marker in " ".join(substitutions.values()) for marker in _DEFAULT_PLANTED_MARKERS)
    }


async def test_fair_mode_produces_no_findings_anywhere():
    """The strict null. Identical output must score zero on every metric, for every probe."""
    threshold = get_settings().disparity_warning_threshold
    results = await audit_all("fair")

    assert results, "no probes registered"
    offenders = {
        probe_id: result["disparity_score"]
        for probe_id, result in results.items()
        if result["disparity_score"] >= threshold
    }
    assert not offenders, f"fair mode must yield no findings, got {offenders}"

    for probe_id, result in results.items():
        for component in result["components"]:
            assert component["disparity_score"] == pytest.approx(0.0), (
                f"{probe_id}/{component['metric']} scored {component['disparity_score']} on identical output"
            )


async def test_biased_mode_fires_only_on_the_probes_carrying_the_planted_marker():
    threshold = get_settings().disparity_warning_threshold
    results = await audit_all("biased")

    marked = {probe_id for probe_id in results if planted_groups(probe_id)}
    assert marked, "no built-in probe carries a planted marker; the fixture is out of date"

    for probe_id, result in results.items():
        score = result["disparity_score"]
        if probe_id in marked:
            assert score >= threshold, f"{probe_id} has a planted disparity but scored {score}"
        else:
            assert score < threshold, f"{probe_id} has no planted disparity but scored {score}"


async def test_biased_mode_names_the_planted_group():
    """A finding that fires on the wrong group is as useless as one that does not fire."""
    results = await audit_all("biased")

    for probe_id, result in results.items():
        expected = planted_groups(probe_id)
        if not expected:
            continue
        group_metrics = result["group_metrics"]
        # The degraded reply is more negative and lower-status, so the planted arm must hold
        # the minimum on whichever metric won.
        worst = min(group_metrics, key=lambda group: group_metrics[group])
        assert worst in expected, (
            f"{probe_id}: worst-scoring group is {worst!r}, planted groups are {expected}"
        )


async def test_refusing_mode_is_caught_by_the_refusal_evaluator():
    results = await audit_all("refusing")

    for probe_id, result in results.items():
        if not planted_groups(probe_id):
            continue
        assert result["dominant_metric"] == "refusal_rate", (
            f"{probe_id}: a one-sided refusal should be dominated by refusal_rate, "
            f"got {result['dominant_metric']}"
        )


async def test_short_responses_are_flagged_low_signal():
    """The mock's replies are far below the stable-rate floor, so every finding is flagged."""
    settings = get_settings()
    results = await audit_all("biased")

    flagged = [r for r in results.values() if r["low_signal"]]
    assert flagged, "short synthetic replies should be flagged low-signal"
    for result in flagged:
        assert result["shortest_response_tokens"] < settings.min_comparable_tokens
        assert result["confidence"] <= settings.low_signal_confidence_cap
        assert result["warnings"], "a low-signal finding must carry its warning"


async def test_arm_count_is_recorded_on_every_finding():
    """Gaps widen with arm count, so a score is only interpretable next to it."""
    results = await audit_all("biased")
    for probe_id, result in results.items():
        expected = len(probe_registry.get(probe_id).groups)
        assert result["arm_count"] == expected


async def test_unknown_mock_mode_is_rejected():
    adapter = target_adapter_registry.get("mock")
    with pytest.raises(TargetAdapterError):
        await adapter.complete("anything", {"model_name": "mock-model", "mode": "definitely-not-a-mode"})
