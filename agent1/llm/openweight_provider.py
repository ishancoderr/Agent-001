"""Qwen3-8B with and without the QLoRA adapter, on the openweight-llm service
(llm.models entries with provider: openweight; `path` is the endpoint).

    POST {QWEN_HOST}{path}   X-API-Key: {QWEN_API_KEY}
    {"messages": [...], "max_tokens": N, "temperature": 0.0}
 -> {"model", "content", "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms"}

The service builds the prompt exactly like the training notebooks (Qwen3's
chat template with thinking turned off) and decodes greedily.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import httpx

from ..settings import OPENWEIGHT_TIMEOUT_S


def complete(spec: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int) -> Tuple[str, int, int]:
    response = httpx.post(
        os.environ["QWEN_HOST"].rstrip("/") + spec["path"],
        headers={"X-API-Key": os.environ["QWEN_API_KEY"]},
        json={"messages": messages, "max_tokens": max_tokens, "temperature": 0.0},
        timeout=OPENWEIGHT_TIMEOUT_S,
    )
    response.raise_for_status()
    answer = response.json()
    return ((answer.get("content") or "").strip(), int(answer.get("prompt_tokens") or 0),
            int(answer.get("completion_tokens") or 0))
