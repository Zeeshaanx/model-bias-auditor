# Evaluator Guide

An evaluator defines *how the answers are compared*. It implements `BiasEvaluator` from
`app.evaluators.base` and receives one `ProbeObservation`.

## Required Members

- `id`, `name`, `description`, `metric`
- `evaluate(observation) -> dict`

## Expected Output

```python
{
    "evaluator_id": "sentiment-disparity",
    "metric": "sentiment_balance_per_100_tokens",
    "probe_id": "...", "probe_name": "...", "attribute": "gender",
    "disparity_score": 0.42,          # 0.0 - 1.0
    "severity": "high",
    "confidence": 0.78,
    "biased": True,
    "group_metrics": {"female": -4.76, "male": 2.70},
    "widest_gap": {"lowest_group": "female", "highest_group": "male"},
    "summary": "one sentence a reviewer can read",
    "evidence": {"excerpts": {...}, "errors": {...}},
}
```

## Building Blocks

`app.evaluators.metrics` holds the measurement functions - all pure, all unit-tested:

- `is_refusal(text)`
- `lexicon_rate(text, terms)` - occurrences per 100 tokens
- `sentiment_balance`, `agency_balance`, `status_balance`, `hedging_rate`
- `widest_gap(values)` - spread plus the lowest and highest group
- `bounded_disparity(gap, scale)` and `relative_disparity(values)` - both clamped to 0.0-1.0
- `severity_for(score, warning, critical)` and `confidence_for(groups, texts)`

Reuse them rather than writing new arithmetic, so every metric is normalised the same way.

## Registering

```python
from app.evaluators.registry import evaluator_registry

evaluator_registry.register(MyEvaluator())
```

Pass its `id` as `evaluator_id` when creating an audit. To include it in the default
composite score, add it to `CompositeDisparityEvaluator(components=[...])`.

## Scale Choice

`bounded_disparity` needs a scale: the raw gap that should read as a maximal disparity.
Pick it from observed data, not intuition, and record the reasoning in
[methodology.md](methodology.md). A scale that is too small makes every audit critical;
one that is too large hides real gaps.
