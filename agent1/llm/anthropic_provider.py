"""Claude models (llm.models entries with provider: anthropic), through the
official Anthropic SDK.

Current Claude models think before they answer and that can't be switched
off, so the reply needs room beyond the JSON itself: THINKING_HEADROOM is
added to the caller's max_tokens, and `effort` (settings.yaml, default low —
these are short, well-specified JSON tasks) keeps the thinking brief. A model
entry with `fallbacks: default` lets the API answer with another Claude model
when the chosen one declines; the model that answered is logged.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import anthropic

log = logging.getLogger("agent1.llm.anthropic")

THINKING_HEADROOM = 4000
_client: anthropic.Anthropic | None = None


def complete(spec: Dict[str, Any], messages: List[Dict[str, str]], max_tokens: int) -> Tuple[str, int, int]:
    global _client
    if _client is None:
        from . import credential
        _client = anthropic.Anthropic(api_key=credential("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"))
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    chat = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    request = dict(model=spec["model"], max_tokens=max_tokens + THINKING_HEADROOM, system=system,
                   messages=chat, output_config={"effort": spec.get("effort", "low")})
    if spec.get("fallbacks"):
        response = _client.beta.messages.create(betas=["server-side-fallback-2026-07-01"],
                                                fallbacks=spec["fallbacks"], **request)
    else:
        response = _client.messages.create(**request)

    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        log.warning("       | %s declined the request (category %s)", response.model, category)
    if response.model != spec["model"]:
        log.warning("       | %s answered instead of %s (fallback)", response.model, spec["model"])
    if response.stop_reason == "max_tokens":
        log.warning("       | %s hit max_tokens — the answer may be cut off", response.model)
    text = "".join(block.text for block in response.content if block.type == "text")
    return text.strip(), response.usage.input_tokens, response.usage.output_tokens
