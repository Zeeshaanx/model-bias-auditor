"""Adapter behaviour that affects whether a measurement is valid at all.

The truncation guard exists because of a real audit, not a hypothetical one. Running the
built-in suite against gemini-2.5-flash with maxOutputTokens=2048 returned 29, 81, 38 and
125 words for four byte-identical prompts differing only in a name, and the evaluator
scored that spread as a critical length-and-hedging disparity. The cause was thinking
tokens eating the output budget and the visible answer being cut at a different point each
call. A truncated arm has to be dropped, not measured.
"""

import pytest

from app.services.target_adapters import (
    AnthropicAdapter,
    GeminiAdapter,
    OpenAICompatibleAdapter,
    TargetAdapterError,
    TruncatedResponseError,
)

CONFIG = {"model_name": "test-model", "api_key": "test-key"}


def stub(adapter, payload):
    """Replace the HTTP call with a fixed provider payload."""

    async def _post_json(*args, **kwargs):
        return payload

    adapter._post_json = _post_json
    return adapter


async def test_gemini_truncation_is_an_error_not_a_short_answer():
    adapter = stub(
        GeminiAdapter(),
        {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "The candidate is"}]}}]},
    )
    with pytest.raises(TruncatedResponseError):
        await adapter.complete("prompt", CONFIG)


async def test_gemini_empty_text_is_an_error():
    adapter = stub(GeminiAdapter(), {"candidates": [{"finishReason": "STOP", "content": {"parts": []}}]})
    with pytest.raises(TargetAdapterError):
        await adapter.complete("prompt", CONFIG)


async def test_gemini_complete_response_passes_through():
    adapter = stub(
        GeminiAdapter(),
        {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "A complete answer."}]}}]},
    )
    assert await adapter.complete("prompt", CONFIG) == "A complete answer."


async def test_gemini_disables_thinking_by_default():
    """Thinking tokens count against maxOutputTokens, so they are off unless asked for."""
    captured = {}

    adapter = GeminiAdapter()

    async def _post_json(url, headers, body, timeout):
        captured.update(body)
        return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "ok"}]}}]}

    adapter._post_json = _post_json
    await adapter.complete("prompt", CONFIG)
    assert captured["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}
    assert captured["generationConfig"]["temperature"] == 0

    captured.clear()
    await adapter.complete("prompt", {**CONFIG, "thinking_budget": 512})
    assert captured["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 512}

    captured.clear()
    await adapter.complete("prompt", {**CONFIG, "thinking_budget": None})
    assert "thinkingConfig" not in captured["generationConfig"]


async def test_openai_compatible_truncation_is_an_error():
    adapter = stub(
        OpenAICompatibleAdapter(),
        {"choices": [{"finish_reason": "length", "message": {"content": "The candidate is"}}]},
    )
    with pytest.raises(TruncatedResponseError):
        await adapter.complete("prompt", CONFIG)


async def test_anthropic_truncation_is_an_error():
    adapter = stub(
        AnthropicAdapter(),
        {"stop_reason": "max_tokens", "content": [{"type": "text", "text": "The candidate is"}]},
    )
    with pytest.raises(TruncatedResponseError):
        await adapter.complete("prompt", CONFIG)
