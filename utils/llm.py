"""Provider-neutral LLM wrapper.

OpenAI is used when OPENAI_API_KEY is available. The interface is intentionally
small so Gemini or another provider can be plugged in without changing agents.
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResult:
    data: dict[str, Any]
    used_llm: bool
    provider: str
    error: str | None = None


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = _resolve_provider(provider)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
        self.model = model or _resolve_model(self.provider)

    @property
    def is_configured(self) -> bool:
        if self.provider == "openai":
            return bool(self.openai_api_key)
        if self.provider in {"gemini", "google", "google-genai"}:
            return bool(self.gemini_api_key)
        return False

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        temperature: float = 0.2,
    ) -> LLMResult:
        """Return JSON from the configured model, or a fallback on failure."""

        if not self.is_configured:
            return LLMResult(
                data=deepcopy(fallback),
                used_llm=False,
                provider=self.provider,
                error=f"{self.provider.upper()} API key is not configured.",
            )

        try:
            if self.provider == "openai":
                from openai import OpenAI

                client = OpenAI(api_key=self.openai_api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
            elif self.provider in {"gemini", "google", "google-genai"}:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.gemini_api_key)
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                content = response.text or "{}"
            else:
                return LLMResult(
                    data=deepcopy(fallback),
                    used_llm=False,
                    provider=self.provider,
                    error=f"Provider '{self.provider}' is not supported. Use 'openai' or 'gemini'.",
                )

            parsed = _parse_json(content)
            merged = _deep_merge(fallback, parsed)
            return LLMResult(data=merged, used_llm=True, provider=self.provider)
        except Exception as exc:  # pragma: no cover - depends on external API
            return LLMResult(data=deepcopy(fallback), used_llm=False, provider=self.provider, error=str(exc))


def _resolve_provider(provider: str | None) -> str:
    explicit = (provider or os.getenv("LLM_PROVIDER", "")).strip().lower()
    if explicit:
        return explicit
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    return "openai"


def _resolve_model(provider: str) -> str:
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if provider in {"gemini", "google", "google-genai"}:
        return os.getenv("GEMINI_MODEL", os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"))
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _parse_json(content: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.I | re.M).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Model response was not a JSON object.")
    return parsed


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif value not in (None, "", []):
            result[key] = value
    return result

