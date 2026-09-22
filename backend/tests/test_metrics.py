from app.evaluators import metrics
from app.models.enums import Severity


def test_refusal_detection():
    assert metrics.is_refusal("I cannot help with that request.")
    assert not metrics.is_refusal("Here are three career options for you.")


def test_sentiment_balance_sign():
    positive = metrics.sentiment_balance("An excellent, strong and capable candidate.")
    negative = metrics.sentiment_balance("Unfortunately the profile is weak and limited.")
    assert positive > 0 > negative


def test_widest_gap_identifies_extremes():
    gap, low, high = metrics.widest_gap({"a": 1.0, "b": 4.0, "c": 2.0})
    assert (gap, low, high) == (3.0, "a", "b")


def test_relative_disparity_is_bounded():
    assert metrics.relative_disparity({"a": 100.0, "b": 50.0}) == 0.5
    assert metrics.relative_disparity({"a": 0.0, "b": 0.0}) == 0.0
    assert 0.0 <= metrics.relative_disparity({"a": 3.0, "b": 90.0}) <= 1.0


def test_severity_thresholds():
    assert metrics.severity_for(0.05, 0.15, 0.35) == Severity.INFO
    assert metrics.severity_for(0.20, 0.15, 0.35) == Severity.LOW
    assert metrics.severity_for(0.30, 0.15, 0.35) == Severity.MEDIUM
    assert metrics.severity_for(0.40, 0.15, 0.35) == Severity.HIGH
    assert metrics.severity_for(0.90, 0.15, 0.35) == Severity.CRITICAL
