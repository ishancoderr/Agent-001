"""
A step-by-step record of how one question was answered, for the evaluation.

While a request runs inside `recording()`, every LLM call (classify, extract,
each SQL statement) and every SQL attempt is added to the current Trace:
which model, input and output tokens, milliseconds, and for SQL whether the
statement passed the safety check, whether it ran, and the error if not.
/query returns it when the request asks for "trace": true; /kqml/receive uses
it to report the peer's own token use back in its tell.

Nothing is recorded outside `recording()`, so normal requests pay nothing.
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, List, Optional


class Trace:
    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.llm_calls: List[Dict[str, Any]] = []
        self.sql_attempts: List[Dict[str, Any]] = []
        self.kqml: List[Dict[str, Any]] = []
        self.results: Dict[str, Any] = {}

    def tokens(self) -> Dict[str, int]:
        inp = sum(c["input_tokens"] for c in self.llm_calls)
        out = sum(c["output_tokens"] for c in self.llm_calls)
        return {"input": inp, "output": out, "total": inp + out}

    def to_dict(self) -> Dict[str, Any]:
        stages: Dict[str, Dict[str, Any]] = {}
        for c in self.llm_calls:
            s = stages.setdefault(c["stage"], {"calls": 0, "input_tokens": 0, "output_tokens": 0, "ms": 0.0})
            s["calls"] += 1
            s["input_tokens"] += c["input_tokens"]
            s["output_tokens"] += c["output_tokens"]
            s["ms"] = round(s["ms"] + c["ms"], 1)
        steps: Dict[str, Dict[str, Any]] = {}
        for a in self.sql_attempts:
            key = f'{a["category"]}/{a["step"]}'
            s = steps.setdefault(key, {"step": key, "label": a["label"], "attempts": 0, "passed_check": False,
                                       "ran": False, "first_try_ok": None, "errors": [], "ms": 0.0})
            s["attempts"] += 1
            s["ms"] = round(s["ms"] + a["ms"], 1)
            ok = a["passed_check"] and a["ran"]
            if s["first_try_ok"] is None:
                s["first_try_ok"] = ok
            s["passed_check"] = s["passed_check"] or a["passed_check"]
            s["ran"] = s["ran"] or a["ran"]
            if a["error"]:
                s["errors"].append(a["error"])
        return {
            **self.results,
            "llm_calls": self.llm_calls,
            "llm_by_stage": stages,
            "sql_steps": list(steps.values()),
            "sql_attempts": self.sql_attempts,
            "kqml": {"turns": len(self.kqml), "ms": round(sum(k["ms"] for k in self.kqml), 1),
                     "peer_tokens": sum(k["peer_tokens"] for k in self.kqml), "exchanges": self.kqml},
            "tokens": self.tokens(),
            "ms": round((time.perf_counter() - self.started) * 1000, 1),
        }


_current: ContextVar[Optional[Trace]] = ContextVar("eval_trace", default=None)


@contextmanager
def recording() -> Iterator[Trace]:
    trace = Trace()
    token = _current.set(trace)
    try:
        yield trace
    finally:
        _current.reset(token)


def active() -> Optional[Trace]:
    return _current.get()


def record_llm(stage: str, model: str, input_tokens: int, output_tokens: int, ms: float, **meta: Any) -> None:
    t = _current.get()
    if t is not None:
        t.llm_calls.append({"stage": stage, "model": model, "input_tokens": int(input_tokens),
                            "output_tokens": int(output_tokens), "ms": round(ms, 1), **meta})


def record_sql(category: str, step: str, label: str, attempt: int, passed_check: bool, ran: bool,
               rows: Optional[int], error: Optional[str], ms: float) -> None:
    t = _current.get()
    if t is not None:
        t.sql_attempts.append({"category": category, "step": step, "label": label, "attempt": attempt,
                               "passed_check": passed_check, "ran": ran, "rows": rows,
                               "error": (error or "")[:300] or None, "ms": round(ms, 1)})


def record_kqml(peer: str, ms: float, peer_tokens: int, ok: bool) -> None:
    """One ask → tell round trip to a peer agent."""
    t = _current.get()
    if t is not None:
        t.kqml.append({"peer": peer, "ms": round(ms, 1), "peer_tokens": int(peer_tokens or 0), "ok": ok})


def record(key: str, value: Any) -> None:
    """A stage's result, e.g. record("classify", "DIRECT_LOOKUP")."""
    t = _current.get()
    if t is not None:
        t.results[key] = value
