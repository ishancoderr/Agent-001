"""
Check a fine-tuning JSONL file without reading it.

Every example is run through the same code the pipeline uses, so a label that
the agent itself would reject fails here:

  all       three messages (system, user, assistant); the assistant reply is JSON
  all       the system prompt is what the loaders build TODAY (catches data
            generated before a prompt YAML was edited)
  classify  the label is a valid category
  extract   the label goes through QueryParamsBuilder.build() with no warning
            and no fallback, and comes out as the expected query_type;
            attributes exist; state names are among the sixteen
  sql       validate_sql() passes; every placeholder is one Python binds
  question  classify and extract of the same question agree
  dataset   no duplicates; the same input never has two different answers;
            no example longer than the training sequence length

Writes <file>_review.csv (opens in Excel) with one row per example — the
input and the answer, no system prompt — for a person to spot-check.

Run from the repo root:
    python -m finetune.check_dataset                      # questions_v1.jsonl
    python -m finetune.check_dataset path/to/file.jsonl --max-tokens 2048
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from agent1.pipeline.gazetteer import GERMAN_STATES, normalize_entity_name
from agent1.pipeline.prompt_loader import CLASSIFY_SYSTEM, EXTRACT_TEMPLATES
from agent1.pipeline.query_params import VALID_QUERY_TYPES
from agent1.pipeline.query_parser import VALID_ATTRS, QueryParamsBuilder
from agent1.retrieval.sql_writer import _PLACEHOLDER, SqlWriter, validate_sql

HERE = Path(__file__).resolve().parent
CHARS_PER_TOKEN = 3.5          # rough for German/English + SQL; no tokenizer needed

_sql_writer = SqlWriter(client=object())


# ═══════════════════════════════════════════════════════════════════════════
# Parser harness — run a label through QueryParamsBuilder and catch complaints
# ═══════════════════════════════════════════════════════════════════════════

class _FellBack(Exception):
    pass


class _NoExtractor:
    """build() calls extract() again only when a label is malformed."""
    model = "label"

    def extract(self, *_args, **_kwargs):
        raise _FellBack("parser rejected the label and tried to re-extract")


class _Warnings(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage().strip(" |"))


_warnings = _Warnings()
logging.getLogger("agent1").addHandler(_warnings)
logging.getLogger("agent1").setLevel(logging.INFO)
logging.getLogger("agent1").propagate = False      # keep the report readable


# ═══════════════════════════════════════════════════════════════════════════
# Checks — each returns a list of problems (empty = pass)
# ═══════════════════════════════════════════════════════════════════════════

def check_shape(ex: Dict[str, Any]) -> List[str]:
    roles = [m.get("role") for m in ex.get("messages", [])]
    if roles != ["system", "user", "assistant"]:
        return [f"messages roles are {roles}, expected system/user/assistant"]
    try:
        json.loads(ex["messages"][2]["content"])
    except json.JSONDecodeError as exc:
        return [f"assistant reply is not JSON: {exc}"]
    return []


def check_prompt_fresh(ex: Dict[str, Any]) -> List[str]:
    meta, system = ex["meta"], ex["messages"][0]["content"]
    if meta["task"] == "classify":
        current = CLASSIFY_SYSTEM
    elif meta["task"] == "extract":
        current = EXTRACT_TEMPLATES.get(meta["category"], "")
        system = system.split("\n\nCURRENT_YEAR =")[0]          # the year is added per call
    else:
        current = _sql_writer._system_prompt(meta["category"], meta["step"])
    return [] if system == current else ["system prompt differs from today's prompt — regenerate"]


def check_classify(ex: Dict[str, Any]) -> List[str]:
    label = json.loads(ex["messages"][2]["content"]).get("query_type")
    problems = []
    if label not in VALID_QUERY_TYPES:
        problems.append(f"query_type {label!r} is not a valid category")
    if label != ex["meta"]["category"]:
        problems.append(f"label {label!r} != meta category {ex['meta']['category']!r}")
    return problems


def check_extract(ex: Dict[str, Any]) -> List[str]:
    meta = ex["meta"]
    data = json.loads(ex["messages"][2]["content"])
    query = ex["messages"][1]["content"].removeprefix("Query: ")
    expected = meta.get("expect_query_type", meta["category"])
    problems = []

    _warnings.messages.clear()
    try:
        params, _ = QueryParamsBuilder(_NoExtractor()).build(
            cleaned_query=query, query_type=meta["category"], data=data, original_query=query,
            tokens_classify=0, tokens_consumed=0, classify_model="label")
    except _FellBack as exc:
        return [str(exc)]
    except Exception as exc:                                     # noqa: BLE001
        return [f"parser crashed: {type(exc).__name__}: {exc}"]
    # The "no year" warning is how the parser produces NEEDS_YEAR, so it is
    # expected exactly when NEEDS_YEAR is the expected outcome.
    expected_warnings = ("no year was named",) if expected == "NEEDS_YEAR" else ()
    problems += [f"parser warning: {w}" for w in _warnings.messages
                 if not any(e in w for e in expected_warnings)]
    if params.query_type != expected:
        problems.append(f"parser produced {params.query_type}, expected {expected}")

    unknown = [a for a in data.get("attributes", []) or [] if a not in VALID_ATTRS]
    if unknown:
        problems.append(f"unknown attribute(s) {unknown}")
    if meta["category"] == "DIRECT_LOOKUP" and data.get("entity_type", "state") == "state":
        spatial = data.get("spatial")
        if spatial != "all":
            bad = [n for n in spatial or [] if normalize_entity_name(n, "state") not in GERMAN_STATES]
            if bad:
                problems.append(f"not one of the sixteen states: {bad}")

    # Every name in the label must be in the question the model saw — catches
    # a label copied from another question. Translated names (Bavaria ->
    # Bayern) are marked in the YAML and skipped.
    if not meta.get("names_translated"):
        absent = [n for n in _label_names(data) if n.lower() not in query.lower()]
        if absent:
            problems.append(f"name(s) not in the question text: {absent}")
    return problems


def _label_names(data: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    spatial = data.get("spatial")
    if isinstance(spatial, list):
        names += spatial
    names += [e.get("entity_name", "") for e in data.get("entities", []) or []]
    rel = data.get("spatial_relationship") or {}
    names += list(rel.get("refs") or []) + ([rel["subject"]] if rel.get("subject") else [])
    return [n for n in names if n]


def check_sql(ex: Dict[str, Any]) -> List[str]:
    sql = json.loads(ex["messages"][2]["content"]).get("sql", "")
    if not sql:
        return ["no 'sql' in the answer"]
    try:
        validate_sql(sql)
    except Exception as exc:                                     # noqa: BLE001
        return [f"validate_sql: {exc}"]
    bind = ex["meta"].get("bind")
    if bind is None:
        return ["meta has no 'bind' list — regenerate with the current builder"]
    unknown = set(_PLACEHOLDER.findall(sql)) - set(bind)
    return [f"placeholder(s) Python does not bind: {sorted(unknown)}"] if unknown else []


TASK_CHECKS = {"classify": check_classify, "extract": check_extract, "sql": check_sql}


def tokens(ex: Dict[str, Any]) -> int:
    return round(sum(len(m["content"]) for m in ex["messages"]) / CHARS_PER_TOKEN)


# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("path", nargs="?", default=str(HERE / "questions_v1.jsonl"))
    ap.add_argument("--max-tokens", type=int, default=2048)
    args = ap.parse_args()

    path = Path(args.path)
    examples = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    failures: Dict[int, List[str]] = {}

    for i, ex in enumerate(examples, 1):
        problems = check_shape(ex)
        if not problems:
            problems += check_prompt_fresh(ex)
            problems += TASK_CHECKS[ex["meta"]["task"]](ex)
            if tokens(ex) > args.max_tokens:
                problems.append(f"≈{tokens(ex)} tokens, over --max-tokens {args.max_tokens}")
        if problems:
            failures[i] = problems

    # Question level: classify and extract of the same qid must agree.
    by_q: Dict[str, Dict[str, str]] = defaultdict(dict)
    for ex in examples:
        if ex["meta"]["task"] in ("classify", "extract"):
            by_q[ex["meta"].get("qid", "?")][ex["meta"]["task"]] = ex["meta"]["category"]
    question_problems = [f"{q}: classify says {d.get('classify')}, extract used {d.get('extract')}"
                         for q, d in by_q.items()
                         if d.get("classify") != d.get("extract")
                         and not (d.get("classify") == "UNRELATED" and "extract" not in d)]

    # Dataset level: duplicates, and the same input with two different answers.
    # For classify the category IS the answer, so it is left out of the key.
    seen: Dict[tuple, set] = defaultdict(set)
    for ex in examples:
        m = ex["meta"]
        category = "" if m["task"] == "classify" else m["category"]
        seen[(m["task"], category, m.get("step"), ex["messages"][1]["content"])].add(
            ex["messages"][2]["content"])
    conflicts = [k for k, answers in seen.items() if len(answers) > 1]
    duplicates = len(examples) - len(seen) - sum(len(a) - 1 for a in seen.values())

    # ── Report ────────────────────────────────────────────────────────────────
    passed = len(examples) - len(failures)
    print(f"\n{path.name}: {len(examples)} examples, {len(by_q)} questions")
    print(f"  passed {passed}   failed {len(failures)}\n")

    counts = Counter((e["meta"]["task"], e["meta"]["category"], e["meta"].get("step", "")) for e in examples)
    print(f"  {'task':<9}{'category':<30}{'step':<15}{'count':>6}")
    for (task, cat, step), n in sorted(counts.items()):
        print(f"  {task:<9}{cat:<30}{step:<15}{n:>6}")

    lengths = defaultdict(list)
    for e in examples:
        lengths[e["meta"]["task"]].append(tokens(e))
    print("\n  length (≈tokens)  " + "   ".join(f"{t}: max {max(v)}, mean {sum(v) // len(v)}"
                                             for t, v in lengths.items()))
    print(f"  duplicates: {duplicates}   conflicting answers for the same input: {len(conflicts)}")

    if failures or question_problems or conflicts:
        print("\nPROBLEMS")
        for i, probs in failures.items():
            m = examples[i - 1]["meta"]
            print(f"  line {i} ({m.get('qid')} {m['task']} {m['category']} {m.get('step', '')}):")
            for p in probs:
                print(f"      - {p}")
        for p in question_problems:
            print(f"  {p}")
        for task, cat, step, user in conflicts:
            print(f"  conflict ({task} {cat} {step or ''}): {user[:80]!r} has {len(seen[(task, cat, step, user)])} answers")

    # ── Spreadsheet for spot-checks ───────────────────────────────────────────
    out = path.with_name(path.stem + "_review.csv")
    with out.open("w", encoding="utf-8-sig", newline="") as fh:     # utf-8-sig: Excel shows ü/ß
        w = csv.writer(fh)
        w.writerow(["line", "qid", "task", "category", "step", "check", "model sees", "model must answer"])
        for i, e in enumerate(examples, 1):
            m = e["meta"]
            w.writerow([i, m.get("qid"), m["task"], m["category"], m.get("step", ""),
                        "; ".join(failures[i]) if i in failures else "ok",
                        e["messages"][1]["content"], e["messages"][2]["content"]])
    print(f"\nReview sheet: {out}")
    sample = sorted(random.Random(0).sample(range(1, len(examples) + 1), min(10, len(examples))))
    print(f"Spot-check these lines by hand: {sample}")


if __name__ == "__main__":
    main()
