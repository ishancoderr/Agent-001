"""
Stage 2 of parsing: pull the fields out of a query, given its category.

The category is already settled by the time this runs, so the model gets one
prompt written for that category alone and only has to fill in its schema —
"copy what you see" rather than "work out what this is". gpt-4o-mini is enough
for that, which is why the expensive model is confined to stage 1.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any, Dict, Tuple

import openai

from .prompt_loader import EXTRACT_TEMPLATES

from .. import llm

log = logging.getLogger("agent1.pipeline.extractor")

# The model is the one the request chose (agent1/llm, config/settings.yaml).
MAX_TOKENS = 600      # an "all states" geometry answer needs the room


class QueryExtractor:
    """Fills in one category's fields using that category's own prompt."""

    def __init__(self, client: openai.OpenAI | None = None):
        """`client`: an OpenAI client to reuse when the chosen model is an
        OpenAI one (made from the env key otherwise)."""
        self._client = client

    @property
    def model(self) -> str:
        """The model id answering this request (agent1/llm)."""
        return llm.current()

    def extract(self, query: str, query_type: str) -> Tuple[Dict[str, Any], int]:
        """Return (fields, tokens_used).

        `query_type` reaches here already validated by QueryClassifier — it's
        always one of VALID_QUERY_TYPES, and UNRELATED never reaches
        extraction (pipeline_main.run() short-circuits on it
        first) — so every value here should already have a real template.
        If one doesn't, that's a real bug (a category with no matching
        config/prompts/*.yaml file), and guessing DIRECT_LOOKUP's prompt
        would silently extract the wrong shape instead of surfacing it."""
        if query_type not in EXTRACT_TEMPLATES:
            raise ValueError(
                f"No extraction template for query_type={query_type!r} — "
                f"add one to config/prompts/ (see prompt_loader.py)."
            )
        system_prompt = EXTRACT_TEMPLATES[query_type]
        # Resolved fresh on every call rather than baked into the static
        # template text, so "this year" always means the actual current year,
        # not whatever year happened to be hardcoded when the prompt was written.
        system_prompt += f"\n\nCURRENT_YEAR = {date.today().year}"
        raw, tokens = llm.complete(
            [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Query: {query}"}],
            max_tokens=MAX_TOKENS, client=self._client, stage="extract", category=query_type,
        )
        log.info("       | STEP 1b | Extract (%s, template=%s): %s  (tokens=%d)",
                 self.model, query_type, raw, tokens)

        try:
            data = json.loads(raw)
            from ..evaluation import trace
            trace.record("extract", data)
            return data, tokens
        except json.JSONDecodeError as exc:
            # response_format=json_object makes this very unlikely, but a bad
            # parse must not take the whole query down: an empty dict lets the
            # caller apply its defaults instead.
            log.error("       | STEP 1b | JSON parse failed: %s - raw=%r", exc, raw)
            return {}, tokens
