# Target Adapters

An adapter turns a prompt into a response for one provider. It implements
`complete(prompt, configuration) -> str`.

| Provider | Value | Notes |
| --- | --- | --- |
| Built-in mock | `mock` | Offline, deterministic, no API key. The default. |
| OpenAI | `openai` | `api_key` required |
| OpenAI-compatible | `openai_compatible` | `api_key` and `base_url`; use this for Ollama, vLLM, LM Studio and other local servers |
| Anthropic | `anthropic` | `api_key` required |
| Google Gemini | `google_gemini` | `api_key` required |

## Configuration

Held on the target record and passed straight through:

```json
{
  "name": "Local Llama",
  "provider": "openai_compatible",
  "model_name": "llama3.1:8b",
  "configuration": {
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "temperature": 0,
    "max_tokens": 1024,
    "timeout_seconds": 60
  }
}
```

`temperature: 0` is strongly recommended. Counterfactual comparison assumes the only thing
that varies between arms is the attribute token; sampling noise at a high temperature
becomes indistinguishable from bias.

## The Mock Adapter

`MockTargetAdapter` runs offline with no key and no cost, in one of four modes set with
`mode` in the target configuration.

| Mode | Behaviour | Expected result |
| --- | --- | --- |
| `noisy` (default) | Reply assembled from a fixed skeleton with variation seeded by a hash of the prompt | Findings appear, and they are **artifacts** — the variation is unrelated to the demographic token |
| `fair` | One identical reply for every arm | Zero findings, every component score exactly 0.0 |
| `biased` | Degraded reply (shorter, more negative, lower-status, more hedged) for arms containing a planted marker | A finding on exactly the probes carrying a marker, naming the planted group |
| `refusing` | Refusal for arms containing a planted marker | `refusal_rate` dominant on exactly those probes |

```json
{
  "name": "Calibration - fair",
  "provider": "mock",
  "model_name": "mock-model",
  "configuration": { "mode": "fair" }
}
```

Planted markers default to the minority-group names in the built-in US and EU packs and can
be replaced with `planted_markers`. In `noisy` mode, `"simulate_refusals": true` exercises
the refusal evaluator against synthetic declines.

### What calibration proves, and what it does not

The `fair` and `biased` modes exist because the tool cannot otherwise say anything about
its own scores. With ground truth planted, two claims become testable instead of asserted:
that the evaluators stay silent on identical output, and that they fire on a planted gap
and name the right group. `backend/tests/test_calibration.py` asserts both, so a change that
breaks the measurement fails the build.

That is a real guarantee, and it is narrower than it sounds. **What it proves:** the
evaluators react correctly to a signal planted in synthetic text. **What it does not
prove:** that the metrics are meaningful on real model output — that the lexicons capture
what they claim to, that the scales are calibrated to anything, or that a score of 0.4
means more than a score of 0.3. Those questions need a real target and a human reading the
stored evidence.

Run the whole calibration and see the table for yourself:

```
cd backend
python scripts/calibrate.py
```

## Truncation Is An Error, Not A Short Answer

Every adapter checks whether the provider cut the response off at the token limit
(`finishReason: MAX_TOKENS` for Gemini, `finish_reason: "length"` for OpenAI-compatible,
`stop_reason: "max_tokens"` for Anthropic) and raises `TruncatedResponseError` when it did.
The execution agent records that arm as an error, so it is dropped from the comparison
rather than measured.

This costs one measurement and prevents a wrong one. Every metric here compares arms
against each other, and a response that stopped early is shorter, less hedged and
differently worded than one that finished — for a reason that has nothing to do with the
attribute under test.

The rule came out of a real audit. Running the built-in suite against `gemini-2.5-flash`
with `max_tokens: 2048` returned these four arms for prompts that were byte-identical apart
from one name:

```
majority_de    29 words
turkish        81 words
moroccan       38 words
nigerian      125 words
```

The evaluator scored that spread as a **critical** `length_and_hedging` disparity. It was
measuring how much of the output budget each call happened to have left.

## Gemini And Thinking Tokens

Gemini 2.5 and 3 models think by default, and `maxOutputTokens` counts thinking tokens
against the same budget. Left alone, most of the budget is spent before a word is emitted
and the visible answer is truncated at a different point on every call — which is exactly
what produced the spread above.

**Thinking is therefore disabled by default in this adapter**, by sending
`generationConfig.thinkingConfig.thinkingBudget = 0`. For a counterfactual audit a complete
short answer is worth far more than a truncated reasoned one.

| `thinking_budget` | Effect |
| --- | --- |
| omitted, or `0` | Thinking off. The default. |
| a positive integer | That many thinking tokens. Raise `max_tokens` well above it. |
| `null` | Field omitted entirely; the model's own default applies. |

```json
{
  "name": "Gemini 2.5 Flash",
  "provider": "google_gemini",
  "model_name": "gemini-2.5-flash",
  "configuration": {
    "api_key": "...",
    "temperature": 0,
    "max_tokens": 1024,
    "thinking_budget": 0
  }
}
```

## Adding A Provider

Subclass `TargetAdapter`, set `provider`, implement `complete`, add the value to
`TargetProvider` in `app/models/enums.py`, and register the adapter in
`TargetAdapterRegistry`. Raise `TargetAdapterError` for provider failures so the execution
agent can record them per arm instead of failing the audit.
