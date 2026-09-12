"""Google Gemini backend, presenting the same interface as LLMClient.

Only ``__init__``, ``complete`` and ``count_tokens`` are provider-specific;
``complete_json`` and the ``LLMResult`` contract are inherited from LLMClient, so
every agent and guardrail call site works unchanged when ``LLM_PROVIDER=gemini``.
Claude-only knobs (effort, adaptive thinking, prompt cache, refusal fallbacks)
are accepted for interface parity and ignored - Gemini 2.5 manages its own
thinking.
"""

from __future__ import annotations

import copy
import logging
import time
from typing import Any

from taxpilot.config import Settings, get_settings
from taxpilot.llm.client import LLMClient, LLMResult

logger = logging.getLogger(__name__)

#: Transient server-side statuses worth a short retry. 503 = high demand, 429 =
#: rate/quota spike; both are often gone within a second or two. A quota that is
#: genuinely exhausted keeps returning 429 and simply exhausts the retries, after
#: which the caller falls back to its deterministic path as usual.
_RETRY_STATUSES = (429, 503)
_MAX_ATTEMPTS = 3

#: Gemini finish reasons that mean the model declined. Mapped to the app's
#: "refusal" stop_reason so complete_json raises LLMRefusedError like Claude does.
_REFUSAL_FINISHES = frozenset(
    {
        "SAFETY",
        "PROHIBITED_CONTENT",
        "BLOCKLIST",
        "SPII",
        "RECITATION",
        "IMAGE_SAFETY",
        "IMAGE_PROHIBITED_CONTENT",
    }
)

#: json_schema_for() adds keys Gemini's structured-output validator rejects.
_STRIP_SCHEMA_KEYS = ("additionalProperties", "title", "$schema")


def _gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Strip keys Gemini rejects from a JSON schema.

    Extra fields the model might still emit are harmless: the pydantic model the
    caller validates against ignores unknown keys by default.
    """
    clean = copy.deepcopy(schema)

    def scrub(node: Any) -> None:
        if isinstance(node, dict):
            for key in _STRIP_SCHEMA_KEYS:
                node.pop(key, None)
            for value in node.values():
                scrub(value)
        elif isinstance(node, list):
            for item in node:
                scrub(item)

    scrub(clean)
    return clean


class GeminiClient(LLMClient):
    """Drop-in LLMClient backed by the google-genai SDK."""

    def __init__(self, settings: Settings | None = None) -> None:
        # Deliberately does NOT call super().__init__ - that builds an Anthropic
        # client and would fail without an Anthropic credential.
        from google import genai

        self.settings = settings or get_settings()
        # api_key=None lets the SDK fall back to GOOGLE_API_KEY / GEMINI_API_KEY.
        self._client = genai.Client(api_key=self.settings.google_api_key or None)

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        cache_system: bool = True,
        model: str | None = None,
        effort: str | None = None,
        max_tokens: int | None = None,
        thinking: bool = True,
        history: list[dict[str, Any]] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        from google.genai import types

        chosen_model = model or self.settings.llm_model
        cfg: dict[str, Any] = {"max_output_tokens": max_tokens or self.settings.llm_max_tokens}
        if system:
            cfg["system_instruction"] = system
        if output_schema:
            cfg["response_mime_type"] = "application/json"
            cfg["response_json_schema"] = _gemini_schema(output_schema)

        response = self._generate(
            model=chosen_model,
            contents=self._contents(prompt, history),
            config=types.GenerateContentConfig(**cfg),
        )
        return self._to_result(response, chosen_model)

    def _generate(self, **kwargs: Any) -> Any:
        """generate_content with a short retry on transient 429/503 spikes."""
        from google.genai import errors

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                return self._client.models.generate_content(**kwargs)
            except errors.APIError as exc:
                if getattr(exc, "code", None) not in _RETRY_STATUSES or attempt == _MAX_ATTEMPTS:
                    raise
                wait = 0.75 * attempt
                logger.warning("Gemini %s on %s (attempt %d/%d); retrying in %.1fs",
                               exc.code, kwargs.get("model"), attempt, _MAX_ATTEMPTS, wait)
                time.sleep(wait)

    def count_tokens(self, prompt: str, *, system: str | None = None) -> int:
        contents = [system, prompt] if system else prompt
        response = self._client.models.count_tokens(
            model=self.settings.llm_model, contents=contents
        )
        return int(response.total_tokens or 0)

    # ----------------------------------------------------------------- private

    @staticmethod
    def _contents(prompt: str, history: list[dict[str, Any]] | None) -> list[Any]:
        from google.genai import types

        contents: list[Any] = []
        for message in history or []:
            role = "model" if message.get("role") == "assistant" else "user"
            text = message.get("content")
            if not isinstance(text, str):
                text = str(text)
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
        return contents

    @staticmethod
    def _to_result(response: Any, model: str) -> LLMResult:
        finish: str | None = None
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            raw = getattr(candidates[0], "finish_reason", None)
            finish = getattr(raw, "name", None) or (str(raw) if raw is not None else None)

        try:
            text = response.text or ""
        except Exception:  # .text can raise when the response was blocked
            text = ""

        if finish in _REFUSAL_FINISHES:
            stop_reason = "refusal"
        elif finish == "MAX_TOKENS":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"

        usage = getattr(response, "usage_metadata", None)
        return LLMResult(
            text=text.strip(),
            model=getattr(response, "model_version", None) or model,
            stop_reason=stop_reason,
            refusal_category=finish if stop_reason == "refusal" else None,
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
            cache_read_tokens=getattr(usage, "cached_content_token_count", 0) or 0,
        )
