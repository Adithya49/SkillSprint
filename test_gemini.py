"""Quick smoke test for the provider-aware LLM wrapper."""

from __future__ import annotations

import os

from utils.llm import LLMClient


def main() -> None:
    provider = os.getenv("LLM_PROVIDER", "gemini")
    client = LLMClient(provider=provider)
    result = client.generate_json(
        "Return only valid JSON.",
        'Reply with {"message": "hello", "capital": "Delhi"}.',
        {"message": "fallback", "capital": "Delhi"},
    )
    print(result.data)
    print(f"used_llm={result.used_llm}")
    if result.error:
        print(f"error={result.error}")


if __name__ == "__main__":
    main()