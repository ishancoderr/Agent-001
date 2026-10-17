"""
Stage 1 of parsing: decide which category a query belongs to.

This stage does one thing only — pick one of VALID_QUERY_TYPES — so the prompt
stays small and the model is not also being asked to pull fields out. The
extraction stage then gets a prompt written specifically for that one category.

There is deliberately no regex "safety net" correcting the model here. An
earlier version had one, and measured against the full question set it changed
a correct answer into a wrong one 7 times out of 250: phrasings its patterns
did not anticipate ("Of X and Y, which is within 100 km of Z?", "what towns
fall within 40 km") were forced into the wrong category. A pattern list can
only override the model, never improve it, so the model's answer stands.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Tuple

import openai

from .prompt_loader import CLASSIFY_SYSTEM
from .query_params import VALID_QUERY_TYPES

from .. import llm

log = logging.getLogger("agent1.pipeline.classifier")

# The model is the one the request chose (agent1/llm, config/settings.yaml
# llm.models) — the same for classify, extract and SQL.

# The prompt itself lives in config/prompts/classify.yaml, not here — see
# prompt_loader.py's load_classify_system(). Editing the wording, categories,
# or examples is a YAML edit, not a code change.


def extract_json_object(raw: str) -> Dict[str, Any]:
    """Best-effort JSON parse, kept as a safety net even though the classify
    call itself now requests response_format={"type": "json_object"}. Strips
    markdown fences and falls back to the first {...} block if the model
    wrapped its answer in prose regardless."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {}


class QueryClassifier:
    """Picks the one category that best describes a query."""

    def __init__(self, client: openai.OpenAI | None = None):
        """`client`: an OpenAI client to reuse when the chosen model is an
        OpenAI one (made from the env key otherwise)."""
        self._client = client

    @property
    def model(self) -> str:
        """The model id answering this request (agent1/llm)."""
        return llm.current()

    def classify(self, query: str) -> Tuple[str, int]:
        """Return (query_type, tokens_used).

        An unrecognised answer falls back to DIRECT_LOOKUP, which is the only
        category that can answer something without further structure."""
        raw, tokens = llm.complete(
            [{"role": "system", "content": CLASSIFY_SYSTEM}, {"role": "user", "content": query}],
            max_tokens=20, client=self._client,
        )
        log.info("       | STEP 1a | Classify (%s): %s  (tokens=%d)", self.model, raw, tokens)

        data = extract_json_object(raw)
        if not data:
            log.error("       | STEP 1a | Could not parse JSON from classify response - raw=%r", raw)

        query_type = data.get("query_type", "DIRECT_LOOKUP")
        if query_type not in VALID_QUERY_TYPES:
            log.warning("       | STEP 1a | Unknown query_type %r - defaulting to DIRECT_LOOKUP",
                        query_type)
            query_type = "DIRECT_LOOKUP"
        return query_type, tokens
