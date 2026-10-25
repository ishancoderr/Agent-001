"""
From stored asks to the numbers the thesis reports, and the CSV files.

Verdict on an answer (the final-answer correctness):
    confirmed   someone marked this answer (question + fingerprint) correct or
                wrong in the Evaluation tab — every ask that gave the same
                answer, in any run or model, shares that verdict
    automatic   the agent returned an HTTP error: no answer, so wrong
    unreviewed  not judged yet; the suggestion says whether it differs from an
                answer already confirmed correct for that question

Per question × model (primary agent's asks):
    consistency  share of the repeats that gave the most common answer
    symmetric    the peer's answer equals the primary's first answer
"""
from __future__ import annotations

import csv
import io
import json
import statistics
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional

from . import store
from .scoring import consistency, kqml_messages


# ── verdicts ─────────────────────────────────────────────────────────────────

def annotate(asks: List[Dict[str, Any]], verdicts: Dict[tuple, Dict[str, Any]]) -> None:
    """Adds answer_verdict / verdict_source / suggestion to each finished ask."""
    correct_fps = defaultdict(set)
    for (qid, fp), v in verdicts.items():
        if v["verdict"] == "correct":
            correct_fps[qid].add(fp)
    for a in asks:
        a["answer_verdict"] = a["verdict_source"] = a["suggestion"] = None
        if a["status"] not in ("ok", "error"):
            continue
        fp = a.get("fingerprint") or ""
        v = verdicts.get((a["qid"], fp))
        if v:
            a["answer_verdict"], a["verdict_source"] = v["verdict"], "confirmed"
        elif fp.startswith("error-") or a["status"] == "error":
            a["answer_verdict"], a["verdict_source"] = "wrong", "automatic"
        else:
            a["verdict_source"] = "unreviewed"
            a["suggestion"] = ("differs from the confirmed answer" if correct_fps[a["qid"]]
                               else "no confirmed answer yet")


# ── small helpers ────────────────────────────────────────────────────────────

def _rate(values: Iterable[Optional[int]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(statistics.fmean(vals), 1) if vals else None


def _median(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(statistics.median(vals), 1) if vals else None


def _p95(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = sorted(v for v in values if v is not None)
    return round(vals[min(len(vals) - 1, int(round(0.95 * (len(vals) - 1))))], 1) if vals else None


def _sum(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(sum(vals), 6) if vals else None


def _sql_ok(a: Dict[str, Any]) -> Optional[int]:
    if not a.get("sql_steps"):
        return None
    return int(bool(a.get("sql_passed_check")) and bool(a.get("sql_ran")))


def _verdict_ok(a: Dict[str, Any]) -> Optional[int]:
    return {"correct": 1, "wrong": 0}.get(a.get("answer_verdict") or "")


def _measures(asks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The correctness, token and time measures over a set of finished asks."""
    return {
        "asks": len(asks),
        "http_errors": sum(a["status"] == "error" for a in asks),
        "category_accuracy": _rate(a.get("category_ok") for a in asks),
        "extraction_accuracy": _rate(a.get("extract_ok") for a in asks),
        "sql_first_try_rate": _rate(a.get("sql_first_try_ok") for a in asks if a.get("sql_steps")),
        "sql_passed_check_rate": _rate(a.get("sql_passed_check") for a in asks if a.get("sql_steps")),
        "sql_ran_rate": _rate(a.get("sql_ran") for a in asks if a.get("sql_steps")),
        "sql_ok_rate": _rate(_sql_ok(a) for a in asks),
        "answers_reviewed": sum(_verdict_ok(a) is not None for a in asks),
        "answers_unreviewed": sum(a.get("verdict_source") == "unreviewed" for a in asks),
        "answer_accuracy": _rate(_verdict_ok(a) for a in asks),
        "tokens_in_mean": _mean(a.get("tokens_in") for a in asks),
        "tokens_out_mean": _mean(a.get("tokens_out") for a in asks),
        "peer_tokens_mean": _mean(a.get("peer_tokens") for a in asks),
        "tokens_total_mean": _mean(a.get("tokens_total") for a in asks),
        "tokens_total_sum": _sum(a.get("tokens_total") for a in asks),
        "cost_usd_sum": _sum(a.get("cost_usd") for a in asks),
        "cost_usd_mean": (lambda s, n: round(s / n, 6) if s is not None and n else None)(
            _sum(a.get("cost_usd") for a in asks), sum(a.get("cost_usd") is not None for a in asks)),
        "wall_ms_mean": _mean(a.get("wall_ms") for a in asks),
        "wall_ms_median": _median(a.get("wall_ms") for a in asks),
        "wall_ms_p95": _p95(a.get("wall_ms") for a in asks),
        "ms_classify_mean": _mean(a.get("ms_classify") for a in asks),
        "ms_extract_mean": _mean(a.get("ms_extract") for a in asks),
        "ms_sql_mean": _mean(a.get("ms_sql") for a in asks),
        "ms_kqml_mean": _mean(a.get("ms_kqml") for a in asks),
        "kqml_turns_mean": _mean(a.get("kqml_turns") for a in asks),
        "sql_steps_mean": _mean(a.get("sql_steps") for a in asks),
    }


# ── the tables ───────────────────────────────────────────────────────────────

def load(run_ids: List[int]) -> List[Dict[str, Any]]:
    asks = store.asks_of(run_ids)
    annotate(asks, store.verdicts())
    labels = {r["id"]: r["label"] for r in store.list_runs()}
    for a in asks:
        a["run_label"] = labels.get(a["run_id"])
    return asks


def _done(asks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [a for a in asks if a["status"] in ("ok", "error")]


def per_question(asks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for a in _done(asks):
        groups[(a["model"], a["qid"])].append(a)
    out = []
    for (model, qid), group in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        primary = sorted([a for a in group if a["agent"] == "primary"], key=lambda a: (a["run_id"], a["rep"]))
        peer = [a for a in group if a["agent"] == "peer"]
        fps = [a["fingerprint"] for a in primary]
        first = primary[0] if primary else None
        sym = None
        if first and peer:
            sym = int(peer[0]["fingerprint"] == first["fingerprint"])
        top = Counter(fps).most_common(1)[0][0] if fps else None
        out.append({
            "model": model, "qid": qid, "question": group[0]["question"],
            "expected_category": group[0]["expected_category"],
            "n_places": group[0]["n_places"], "n_years": group[0]["n_years"],
            "n_attributes": group[0]["n_attributes"],
            **_measures(primary),
            "distinct_answers": len(set(fps)),
            "consistency": round(consistency(fps), 4) if fps else None,
            "most_common_answer": next((a["answer_summary"] for a in primary if a["fingerprint"] == top), None),
            "first_answer_verdict": first.get("answer_verdict") if first else None,
            "symmetric": sym,
            "peer_answer": peer[0]["answer_summary"] if peer else None,
            "peer_answer_verdict": peer[0].get("answer_verdict") if peer else None,
        })
    return out


def _model_rows(asks: List[Dict[str, Any]], key) -> List[Dict[str, Any]]:
    questions = per_question(asks)
    by_q: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for q in questions:
        by_q[key(q)].append(q)
    groups: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for a in _done(asks):
        if a["agent"] == "primary":
            groups[key(a)].append(a)
    rows = []
    for k in sorted(set(groups) | set(by_q), key=str):
        qs = by_q.get(k, [])
        repeated = [q["consistency"] for q in qs if q["asks"] > 1 and q["consistency"] is not None]
        compared = [q["symmetric"] for q in qs if q["symmetric"] is not None]
        peer_ok = [{"correct": 1, "wrong": 0}.get(q["peer_answer_verdict"] or "") for q in qs]
        rows.append({
            **(dict(zip(("model", "expected_category"), k)) if isinstance(k, tuple) else {"model": k}),
            "questions": len(qs),
            **_measures(groups.get(k, [])),
            "consistency_mean": round(statistics.fmean(repeated), 4) if repeated else None,
            "fully_consistent_share": round(sum(c == 1 for c in repeated) / len(repeated), 4) if repeated else None,
            "questions_repeated": len(repeated),
            "symmetry_rate": round(sum(compared) / len(compared), 4) if compared else None,
            "symmetry_compared": len(compared),
            "peer_answer_accuracy": _rate(peer_ok),
        })
    return rows


def per_model(asks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _model_rows(asks, key=lambda r: r["model"])


def per_category(asks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _model_rows(asks, key=lambda r: (r["model"], r["expected_category"]))


def steps(run_ids: List[int]) -> List[Dict[str, Any]]:
    """Every LLM call, SQL attempt and KQML round trip of every ask."""
    out = []
    for a in store.asks_of(run_ids, with_response=True):
        t = (store.unpack(a["response_z"]) or {}).get("trace") or {}
        base = {"run_id": a["run_id"], "ask_id": a["id"], "model": a["model"], "agent_name": a["agent_name"],
                "rep": a["rep"], "qid": a["qid"]}
        for i, c in enumerate(t.get("llm_calls") or [], 1):
            out.append({**base, "kind": "llm", "n": i, "stage": c.get("stage"), "category": c.get("category"),
                        "step": c.get("step"), "llm": c.get("model"), "input_tokens": c.get("input_tokens"),
                        "output_tokens": c.get("output_tokens"), "ms": c.get("ms")})
        for i, s in enumerate(t.get("sql_attempts") or [], 1):
            out.append({**base, "kind": "sql", "n": i, "stage": "sql", "category": s.get("category"),
                        "step": s.get("step"), "attempt": s.get("attempt"), "passed_check": int(s["passed_check"]),
                        "ran": int(s["ran"]), "rows": s.get("rows"), "error": s.get("error"), "ms": s.get("ms")})
        for i, k in enumerate((t.get("kqml") or {}).get("exchanges") or [], 1):
            msgs = kqml_messages({"kqml": {"exchanges": [k]}})
            out.append({**base, "kind": "kqml", "n": i, "stage": "kqml", "peer": k.get("peer"),
                        "peer_tokens": k.get("peer_tokens"), "ok": int(bool(k.get("ok"))), "ms": k.get("ms"),
                        "kqml_sent": msgs["kqml_sent"], "kqml_received": msgs["kqml_received"]})
    return out


ASK_COLUMNS = [
    "run_id", "run_label", "id", "model", "agent_name", "rep", "qid", "question", "expected_category",
    "category_got", "category_ok", "extract_ok", "extract_diff",
    "sql_steps", "sql_attempts", "sql_first_try_ok", "sql_passed_check", "sql_ran", "sql_errors",
    "answer_status", "answer_type", "answer_summary", "fingerprint", "answer_verdict", "verdict_source", "suggestion",
    "tokens_in", "tokens_out", "peer_tokens", "tokens_total", "cost_usd",
    "wall_ms", "ms_agent", "ms_classify", "ms_extract", "ms_sql", "ms_kqml", "kqml_turns", "kqml_sent", "kqml_received",
    "llm_calls", "models_used",
    "n_places", "n_years", "n_attributes", "status", "http_status", "error", "tries", "started_at", "finished_at",
]


MODEL_FILE_COLUMNS = [
    "run_id", "run_label", "model", "qid", "question", "agent_name", "rep",
    "expected_category", "category_got", "category_ok", "extract_ok", "extract_diff",
    "sql_steps", "sql_attempts", "sql_first_try_ok", "sql_passed_check", "sql_ran", "sql_errors",
    "answer_status", "answer_summary", "answer_verdict", "verdict_source", "suggestion", "answer_view",
    "question_consistency", "question_distinct_answers", "question_symmetric",
    "tokens_in", "tokens_out", "peer_tokens", "tokens_total", "cost_usd",
    "wall_ms", "ms_agent", "ms_classify", "ms_extract", "ms_sql", "ms_kqml", "kqml_turns", "kqml_sent", "kqml_received",
    "llm_calls",
    "n_places", "n_years", "n_attributes", "fingerprint", "status", "http_status", "error",
    "started_at", "finished_at",
]


def model_file(asks: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Every finished ask of one model, each row also carrying its question's
    consistency and symmetry (the same on every row of that question)."""
    mine = [a for a in asks if a["model"] == model]
    per_q = {q["qid"]: q for q in per_question(mine)}
    rows = []
    for a in _done(mine):
        q = per_q.get(a["qid"], {})
        rows.append({**a, "question_consistency": q.get("consistency"),
                     "question_distinct_answers": q.get("distinct_answers"),
                     "question_symmetric": q.get("symmetric")})
    return rows


def to_csv(rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    if columns is None:
        columns = []
        for r in rows:
            columns += [k for k in r if k not in columns]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list))
                        else round(v, 4) if isinstance(v, float) else v)
                    for k, v in r.items()})
    return "﻿" + buf.getvalue()           # BOM: Excel opens UTF-8 (ü, ß) correctly
