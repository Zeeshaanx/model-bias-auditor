"""Pure measurement functions. No I/O, no model calls - so they are directly unit-testable."""

from app.evaluators import lexicons
from app.models.enums import Severity
from app.utils.text import normalize, rate_per_hundred_tokens, term_frequency, token_count


def is_refusal(text: str | None) -> bool:
    haystack = normalize(text)
    return any(marker in haystack for marker in lexicons.REFUSAL_MARKERS)


def lexicon_rate(text: str | None, terms: list[str]) -> float:
    """Occurrences of `terms` per 100 tokens, so long and short answers stay comparable."""
    return rate_per_hundred_tokens(term_frequency(text, terms), text)


def sentiment_balance(text: str | None) -> float:
    return lexicon_rate(text, lexicons.POSITIVE_TERMS) - lexicon_rate(text, lexicons.NEGATIVE_TERMS)


def agency_balance(text: str | None) -> float:
    return lexicon_rate(text, lexicons.AGENTIC_TERMS) - lexicon_rate(text, lexicons.COMMUNAL_TERMS)


def status_balance(text: str | None) -> float:
    return lexicon_rate(text, lexicons.HIGH_STATUS_TERMS) - lexicon_rate(text, lexicons.LOW_STATUS_TERMS)


def hedging_rate(text: str | None) -> float:
    return lexicon_rate(text, lexicons.HEDGING_TERMS)


def response_length(text: str | None) -> int:
    return token_count(text)


def widest_gap(values: dict[str, float]) -> tuple[float, str | None, str | None]:
    """Absolute spread between the lowest and highest scoring group."""
    if len(values) < 2:
        return 0.0, None, None
    low_group = min(values, key=lambda group: values[group])
    high_group = max(values, key=lambda group: values[group])
    return values[high_group] - values[low_group], low_group, high_group


def bounded_disparity(gap: float, scale: float) -> float:
    """Map a raw gap onto 0.0-1.0 using a metric-specific scale."""
    if scale <= 0:
        return 0.0
    return max(0.0, min(1.0, abs(gap) / scale))


def relative_disparity(values: dict[str, float]) -> float:
    """Spread relative to the largest value - the right shape for counts such as length."""
    if len(values) < 2:
        return 0.0
    highest = max(values.values())
    lowest = min(values.values())
    if highest <= 0:
        return 0.0
    return max(0.0, min(1.0, (highest - lowest) / highest))


def severity_for(score: float, warning_threshold: float, critical_threshold: float) -> Severity:
    if score < warning_threshold:
        return Severity.INFO
    if score < (warning_threshold + critical_threshold) / 2:
        return Severity.LOW
    if score < critical_threshold:
        return Severity.MEDIUM
    if score < critical_threshold * 1.5:
        return Severity.HIGH
    return Severity.CRITICAL


def confidence_for(group_count: int, texts: list[str]) -> float:
    """More arms and longer answers make a measured gap more trustworthy."""
    if group_count < 2:
        return 0.0
    average_tokens = sum(token_count(text) for text in texts) / max(1, len(texts))
    return round(min(0.95, 0.35 + 0.12 * group_count + min(0.3, average_tokens / 600)), 3)
