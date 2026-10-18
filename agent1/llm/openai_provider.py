"""OpenAI models (llm.models entries with provider: openai)."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import openai

_client: openai.OpenAI | None = None


def complete(spec: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int,
             client: openai.OpenAI | None = None) -> Tuple[str, int, int]:
    global _client
    if client is None:
        if _client is None:
            _client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        client = _client
    # JSON mode unless the model doesn't support it (settings.yaml json_mode: false)
    json_mode = {"response_format": {"type": "json_object"}} if spec.get("json_mode", True) else {}
    response = client.chat.completions.create(
        model=spec["model"],
        max_tokens=max_tokens,
        temperature=0,
        messages=messages,
        **json_mode,
    )
    text = (response.choices[0].message.content or "").strip()
    u = response.usage
    return text, (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)
