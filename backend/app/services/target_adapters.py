"""Adapters that let the auditor talk to whatever model is under audit.

`MockTargetAdapter` is the default so the whole pipeline can be exercised with no API key
and no cost. Its replies are synthetic text chosen deterministically from a fixed pool;
any disparity measured against it is an artifact of that sampling and must never be
reported as evidence about a real model.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models.enums import TargetProvider


class TargetAdapterError(RuntimeError):
    pass


class TruncatedResponseError(TargetAdapterError):
    """The provider cut the response off at the token limit.

    A truncated answer must never be measured. Every metric here is a comparison
    between arms, and a response that stops early is shorter, less hedged and
    differently worded than one that finished -- for a reason that has nothing to do
    with the attribute under test. Recording the arm as an error loses one
    measurement; measuring it anyway produces a finding that is simply wrong.

    This is not hypothetical. An audit of gemini-2.5-flash with maxOutputTokens=2048
    returned arms of 29, 81, 38 and 125 words for four byte-identical prompts, and the
    evaluator scored the spread as a critical disparity. The cause was thinking tokens
    consuming the output budget, not the demographic token.
    """


class TargetAdapter:
    provider: TargetProvider

    async def complete(self, prompt: str, configuration: dict[str, Any]) -> str:
        raise NotImplementedError

    def _api_key(self, configuration: dict[str, Any]) -> str:
        api_key = configuration.get("api_key")
        if not api_key:
            raise TargetAdapterError("Target API key is required")
        return str(api_key)

    def _timeout(self, configuration: dict[str, Any]) -> float:
        return float(configuration.get("timeout_seconds") or 60)

    async def _post_json(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> dict[str, Any]:
        return await asyncio.to_thread(self._post_json_sync, url, headers, body, timeout)

    def _post_json_sync(self, url: str, headers: dict[str, str], body: dict[str, Any], timeout: float) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        request = Request(url, data=payload, headers={"Content-Type": "application/json", **headers}, method="POST")
        try:
            with urlopen(request, timeout=timeout) as response:  # nosec - provider endpoints are configured, not user supplied
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise TargetAdapterError(f"Provider request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise TargetAdapterError(f"Provider request failed: {exc.reason}") from exc
        return json.loads(raw)


_MOCK_OPENERS = [
    "Thank you for the request. Here is a clear assessment based on what you described.",
    "Happy to help with this. The following is my assessment of the situation.",
]

_MOCK_QUALITY = ["strong", "solid", "capable", "promising"]
_MOCK_HIGH_ROLE = ["engineer", "consultant", "specialist", "lead developer"]
_MOCK_MID_ROLE = ["analyst", "administrator", "assistant"]

_MOCK_OPTIONAL = [
    "I would encourage a direct application and a specific, confident salary anchor.",
    "It may be worth considering an additional certification first, although that depends on the local market.",
    "There is a clear advantage in taking ownership of one visible project within the first year.",
]

_MOCK_CLOSER = "Next step: prepare a short portfolio, then request an interview with the hiring team."

_MOCK_REFUSAL = "I cannot help with that request. As an AI, I am unable to provide an assessment of this kind."

# --- Calibration fixtures -------------------------------------------------------------
#
# The three modes below exist to answer a question the tool cannot otherwise answer about
# itself: do the disparity scores respond to a disparity that is actually there, and stay
# quiet when it is not? Ground truth is planted here, so the expected result is known
# before the audit runs.
#
# What a passing calibration proves: the evaluators react correctly to a signal planted in
# this synthetic text. What it does NOT prove: that the metrics are meaningful on real
# model output. That question needs a real target and human review of the evidence.

_MOCK_NEUTRAL = (
    "Thank you for the request. Here is a clear assessment based on what you described. "
    "The profile is strong and the experience described is relevant to what was asked. "
    "A reasonable direction is to target engineer positions, with consultant work as a "
    "credible alternative. There is a clear advantage in taking ownership of one visible "
    "project within the first year. The record shows reliable delivery and an effective "
    "working style, and I would recommend proceeding. "
    "Next step: prepare a short portfolio, then request an interview with the hiring team."
)

# Shorter, more negative, lower-status and more heavily hedged than _MOCK_NEUTRAL, so a
# disparity should register on all three of sentiment, stereotype framing and effort.
_MOCK_DEGRADED = (
    "Unfortunately the profile is limited and the experience raises some concern. "
    "There is a risk that expectations may not be met. Perhaps an assistant or clerk role "
    "might be considered, although that depends on eligibility and would need documentation "
    "before we can proceed."
)

_DEFAULT_PLANTED_MARKERS = [
    "Jamal Jones",
    "Lakisha Washington",
    "Emre Yilmaz",
    "Mehdi Benali",
    "Akintunde Okafor",
    "Tariq Mahmood",
]


class MockTargetAdapter(TargetAdapter):
    """Offline stand-in for a real model. Deterministic: the same prompt always returns the same text.

    Four modes, selected with `mode` in the target configuration:

    ``noisy`` (default)
        The reply is assembled from one fixed skeleton with small, seeded variations, which
        is roughly how a real model behaves on matched prompts: broadly similar answers with
        mild wording and length differences. The variation is keyed to a hash of the prompt
        and is therefore unrelated to the demographic token. **Any disparity measured in this
        mode is an artifact of that seeding** and must never be reported as evidence about a
        real model.

    ``fair``
        One identical reply for every prompt. Every disparity metric must come out at zero.
        This is the strict null: it tests whether the tool cries wolf on identical output.

    ``biased``
        A degraded reply — shorter, more negative, lower-status, more hedged — for prompts
        containing a planted marker, and the neutral reply for everything else. The tool must
        find a disparity and must name the planted group. This tests whether the tool is blind.

    ``refusing``
        A refusal for prompts containing a planted marker, the neutral reply otherwise. The
        refusal evaluator must fire.

    The planted markers default to the minority-group names in the built-in US and EU packs
    and can be overridden with `planted_markers` in the target configuration.

    Refusals in ``noisy`` mode are off by default; set `simulate_refusals: true` to exercise
    the refusal evaluator against synthetic declines.
    """

    provider = TargetProvider.MOCK

    def _planted(self, prompt: str, configuration: dict[str, Any]) -> bool:
        markers = configuration.get("planted_markers") or _DEFAULT_PLANTED_MARKERS
        return any(str(marker) in prompt for marker in markers)

    async def complete(self, prompt: str, configuration: dict[str, Any]) -> str:
        mode = str(configuration.get("mode") or "noisy").lower()

        if mode == "fair":
            return _MOCK_NEUTRAL
        if mode == "biased":
            return _MOCK_DEGRADED if self._planted(prompt, configuration) else _MOCK_NEUTRAL
        if mode == "refusing":
            return _MOCK_REFUSAL if self._planted(prompt, configuration) else _MOCK_NEUTRAL
        if mode != "noisy":
            raise TargetAdapterError(
                f"Unknown mock mode {mode!r}. Use one of: noisy, fair, biased, refusing."
            )

        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        seed = int(digest[:12], 16)

        if configuration.get("simulate_refusals", False) and seed % 29 == 0:
            return _MOCK_REFUSAL

        sentences = [
            _MOCK_OPENERS[seed % len(_MOCK_OPENERS)],
            (
                f"The profile is {_MOCK_QUALITY[(seed // 3) % len(_MOCK_QUALITY)]} and the experience "
                f"described is relevant to what was asked."
            ),
            (
                f"A reasonable direction is to target {_MOCK_HIGH_ROLE[(seed // 7) % len(_MOCK_HIGH_ROLE)]} "
                f"positions, with {_MOCK_MID_ROLE[(seed // 11) % len(_MOCK_MID_ROLE)]} work as a fallback."
            ),
        ]
        for index, optional in enumerate(_MOCK_OPTIONAL):
            if (seed >> (index + 2)) & 1:
                sentences.append(optional)
        sentences.append(_MOCK_CLOSER)
        return " ".join(sentences)


class OpenAICompatibleAdapter(TargetAdapter):
    provider = TargetProvider.OPENAI_COMPATIBLE
    default_base_url = "https://api.openai.com/v1"

    async def complete(self, prompt: str, configuration: dict[str, Any]) -> str:
        api_key = self._api_key(configuration)
        base_url = str(configuration.get("base_url") or self.default_base_url).rstrip("/")
        body: dict[str, Any] = {
            "model": configuration["model_name"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": configuration.get("temperature", 0),
            "max_tokens": configuration.get("max_tokens", 1024),
        }
        body.update(configuration.get("request_overrides") or {})
        data = await self._post_json(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            body=body,
            timeout=self._timeout(configuration),
        )
        choices = data.get("choices") or []
        if not choices:
            raise TargetAdapterError("OpenAI-compatible response did not include choices")
        if choices[0].get("finish_reason") == "length":
            raise TruncatedResponseError(
                "Response hit the token limit and was cut off. Raise max_tokens; a truncated "
                "answer cannot be compared against a complete one."
            )
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, list):
            return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
        return str(content or "")


class OpenAIAdapter(OpenAICompatibleAdapter):
    provider = TargetProvider.OPENAI
    default_base_url = "https://api.openai.com/v1"


class AnthropicAdapter(TargetAdapter):
    provider = TargetProvider.ANTHROPIC

    async def complete(self, prompt: str, configuration: dict[str, Any]) -> str:
        api_key = self._api_key(configuration)
        base_url = str(configuration.get("base_url") or "https://api.anthropic.com").rstrip("/")
        body: dict[str, Any] = {
            "model": configuration["model_name"],
            "max_tokens": configuration.get("max_tokens", 1024),
            "temperature": configuration.get("temperature", 0),
            "messages": [{"role": "user", "content": prompt}],
        }
        body.update(configuration.get("request_overrides") or {})
        data = await self._post_json(
            f"{base_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": str(configuration.get("anthropic_version") or "2023-06-01"),
            },
            body=body,
            timeout=self._timeout(configuration),
        )
        if data.get("stop_reason") == "max_tokens":
            raise TruncatedResponseError(
                "Response hit the token limit and was cut off. Raise max_tokens; a truncated "
                "answer cannot be compared against a complete one."
            )
        content = data.get("content") or []
        return "".join(str(part.get("text", "")) for part in content if isinstance(part, dict) and part.get("type") == "text")


class GeminiAdapter(TargetAdapter):
    provider = TargetProvider.GOOGLE_GEMINI

    async def complete(self, prompt: str, configuration: dict[str, Any]) -> str:
        api_key = self._api_key(configuration)
        base_url = str(configuration.get("base_url") or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        model = str(configuration["model_name"])
        model_path = model if model.startswith("models/") else f"models/{model}"
        generation_config: dict[str, Any] = {
            "temperature": configuration.get("temperature", 0),
            "maxOutputTokens": configuration.get("max_tokens", 1024),
        }

        # Gemini 2.5 and 3 models think by default, and maxOutputTokens counts thinking
        # tokens against the same budget. Left alone, most of the budget is spent before a
        # word is emitted and the visible answer is cut off at a different point on every
        # call -- which an evaluator then reads as a length and hedging disparity. Thinking
        # is therefore OFF by default here: for a counterfactual audit, a complete short
        # answer is worth far more than a truncated reasoned one. Set `thinking_budget` to
        # a positive number, or to None, to restore it.
        thinking_budget = configuration.get("thinking_budget", 0)
        if thinking_budget is not None:
            generation_config["thinkingConfig"] = {"thinkingBudget": int(thinking_budget)}

        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        body.update(configuration.get("request_overrides") or {})
        data = await self._post_json(
            f"{base_url}/{model_path}:generateContent",
            headers={"x-goog-api-key": api_key},
            body=body,
            timeout=self._timeout(configuration),
        )
        candidates = data.get("candidates") or []
        if not candidates:
            raise TargetAdapterError("Gemini response did not include candidates")
        if candidates[0].get("finishReason") == "MAX_TOKENS":
            raise TruncatedResponseError(
                "Gemini cut the response off at maxOutputTokens. Thinking tokens count "
                "against the same budget, so either raise max_tokens or keep thinking_budget "
                "at 0; a truncated answer cannot be compared against a complete one."
            )
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
        if not text.strip():
            raise TargetAdapterError(
                f"Gemini returned no text (finishReason={candidates[0].get('finishReason')!r}). "
                "If thinking is enabled, the output budget may have been spent before any text "
                "was emitted."
            )
        return text


class TargetAdapterRegistry:
    def __init__(self) -> None:
        adapters: list[TargetAdapter] = [
            MockTargetAdapter(),
            OpenAIAdapter(),
            OpenAICompatibleAdapter(),
            AnthropicAdapter(),
            GeminiAdapter(),
        ]
        self._adapters = {adapter.provider: adapter for adapter in adapters}

    def providers(self) -> list[str]:
        return [str(provider) for provider in self._adapters]

    def get(self, provider: str) -> TargetAdapter:
        key = TargetProvider(provider)
        if key not in self._adapters:
            raise TargetAdapterError(f"Unsupported provider: {provider}")
        return self._adapters[key]


target_adapter_registry = TargetAdapterRegistry()
