"""
The question set of a run: the JSON list pasted or uploaded in the
Evaluation tab, one item per question —

    [
      {"question": "What was the population of Hessen in 2019?", "model": "gpt-4o-mini"},
      {"question": "Which states border Bayern?", "model": ["gpt-4o", "claude-haiku"]},
      {"question": "Which states lie south of Hessen?"}
    ]

- `question`  required.
- `model`     a model id or label, a list of them, or "all"/missing = every
              model ticked in step 1. Only ticked models may be named.
- `id`        optional; otherwise derived from the question text, so the same
              question keeps its id (and its confirmed answers) across runs.
- `category`, `extract`  optional: the expected classify label and extraction,
              in the format of finetune/questions_vN.yaml. Without them the
              category and extraction checks are left blank for that question.
              A question that is in the answer key (settings.yaml `test_set`)
              takes its labels from there unless the item gives its own.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from pydantic import BaseModel, Field

from agent1.pipeline.query_params import VALID_QUERY_TYPES

from .config import load_questions

MAX_ERRORS = 15


class Item(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    model: Optional[Union[str, List[str]]] = None
    id: Optional[str] = Field(None, min_length=1, max_length=64)
    category: Optional[str] = Field(None, max_length=64)
    extract: Optional[Dict[str, Any]] = None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).casefold()


def derived_id(question: str) -> str:
    return "q-" + hashlib.sha1(_norm(question).encode("utf-8")).hexdigest()[:10]


def resolve(items: List[Item], models: List[Dict[str, Any]], ticked: List[str]) -> List[Dict[str, Any]]:
    """The items as questions to run: id, question, category, extract and the
    models each runs on. Every problem is reported at once (HTTP 400)."""
    by_name = {}
    for m in models:
        by_name[m["id"].casefold()] = m["id"]
        by_name[m["label"].casefold()] = m["id"]
    key = {_norm(q["question"]): q for q in load_questions()}
    errors: List[str] = []
    out: List[Dict[str, Any]] = []
    seen: Dict[str, str] = {}
    for n, item in enumerate(items, 1):
        where = f"item {n}"
        known = key.get(_norm(item.question), {})
        qid = item.id or known.get("id") or derived_id(item.question)
        if seen.get(qid, item.question) != item.question:
            errors.append(f"{where}: id {qid!r} is already used by another question")
        seen[qid] = item.question

        wanted = item.model if isinstance(item.model, list) else [item.model]
        chosen: List[str] = []
        for name in wanted:
            if name is None or str(name).strip().casefold() == "all":
                chosen += [m for m in ticked if m not in chosen]
                continue
            mid = by_name.get(str(name).strip().casefold())
            if mid is None:
                errors.append(f"{where}: unknown model {name!r}")
            elif mid not in ticked:
                errors.append(f"{where}: model {name!r} is not ticked in step 1")
            elif mid not in chosen:
                chosen.append(mid)

        category = item.category or known.get("category")
        if category is not None and category not in VALID_QUERY_TYPES:
            errors.append(f"{where}: category {category!r} is not one of {sorted(VALID_QUERY_TYPES)}")
        out.append({"id": qid, "question": item.question.strip(), "category": category,
                    "extract": item.extract if item.extract is not None else known.get("extract"),
                    "models": chosen})

    pairs = [(q["id"], m) for q in out for m in q["models"]]
    dupes = sorted({f"{qid} × {m}" for qid, m in pairs if pairs.count((qid, m)) > 1})
    if dupes:
        errors.append(f"the same question and model appear twice: {', '.join(dupes[:5])}"
                      + (" …" if len(dupes) > 5 else "") + " — use the repeats in step 1 instead")
    if errors:
        more = len(errors) - MAX_ERRORS
        raise HTTPException(400, "; ".join(errors[:MAX_ERRORS]) + (f"; and {more} more" if more > 0 else ""))
    return out


def run_questions(plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """The questions of a stored run, by id — what its answers are scored against."""
    if plan.get("resolved"):
        return {q["id"]: q for q in plan["resolved"]}
    return {q["id"]: q for q in load_questions()}
