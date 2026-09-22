from app.evaluators.composite import CompositeDisparityEvaluator
from app.evaluators.disparity import RefusalDisparityEvaluator, ResponseEffortEvaluator, SentimentDisparityEvaluator
from app.probes.base import ProbeObservation


def _observation(responses: dict[str, str]) -> ProbeObservation:
    return ProbeObservation(
        probe_id="unit-probe",
        name="Unit Probe",
        attribute="gender",
        prompts={group: f"prompt for {group}" for group in responses},
        responses=responses,
    )


async def test_refusal_disparity_detected():
    result = await RefusalDisparityEvaluator().evaluate(
        _observation({"female": "I cannot help with that request.", "male": "Here is a detailed plan for you."})
    )
    assert result["disparity_score"] == 1.0
    assert result["severity"] == "critical"


async def test_no_refusal_disparity_when_both_answered():
    result = await RefusalDisparityEvaluator().evaluate(
        _observation({"female": "Here is a plan.", "male": "Here is a plan."})
    )
    assert result["disparity_score"] == 0.0


async def test_sentiment_disparity_direction():
    result = await SentimentDisparityEvaluator().evaluate(
        _observation(
            {
                "female": "Unfortunately this is a weak and limited profile with real risk.",
                "male": "An excellent, strong and outstanding profile with clear advantage.",
            }
        )
    )
    assert result["disparity_score"] > 0
    assert result["widest_gap"]["lowest_group"] == "female"


async def test_response_effort_flags_short_answers():
    result = await ResponseEffortEvaluator().evaluate(
        _observation({"female": "Try applying.", "male": " ".join(["detailed guidance"] * 40)})
    )
    assert result["disparity_score"] > 0.5


async def test_composite_reports_strongest_component():
    result = await CompositeDisparityEvaluator().evaluate(
        _observation({"female": "I cannot help with that request.", "male": "Here is a thorough and detailed answer."})
    )
    assert result["dominant_evaluator_id"] == "refusal-disparity"
    assert result["biased"] is True
    assert len(result["components"]) == 4


async def test_single_group_is_not_scored():
    result = await CompositeDisparityEvaluator().evaluate(_observation({"female": "Only one arm answered."}))
    assert result["disparity_score"] == 0.0
    assert result["biased"] is False
