"""
The results database (SQLite, settings.yaml `database`).

    runs      one evaluation: which models, questions, repeats, symmetry
    asks      every question sent to an agent: planned when the run is
              created, filled in as it runs — the raw response (compressed)
              and the scores computed from it (scoring.score)
    verdicts  the hand-confirmed verdict on one distinct answer to one
              question (question id + answer fingerprint), shared by every
              ask, model and run that gave that same answer

Planning every ask up front is what makes a run resumable: the worker just
takes the next pending one.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import zlib
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from .config import DATABASE

SCORE_COLUMNS = [
    "expected_category", "category_got", "category_ok", "extract_ok", "extract_diff",
    "sql_steps", "sql_attempts", "sql_first_try_ok", "sql_passed_check", "sql_ran", "sql_errors",
    "answer_status", "answer_type", "answer_view", "fingerprint", "answer_summary",
    "tokens_in", "tokens_out", "peer_tokens", "tokens_total", "cost_usd",
    "llm_calls", "models_used", "ms_agent", "ms_classify", "ms_extract", "ms_sql", "ms_kqml", "kqml_turns",
    "n_places", "n_years", "n_attributes",
]
_NUMERIC = {"category_ok", "extract_ok", "sql_steps", "sql_attempts", "sql_first_try_ok", "sql_passed_check",
            "sql_ran", "tokens_in", "tokens_out", "peer_tokens", "tokens_total", "llm_calls", "kqml_turns",
            "n_places", "n_years", "n_attributes"}

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    label       TEXT NOT NULL,
    status      TEXT NOT NULL,          -- queued | running | paused | done | cancelled
    note        TEXT,                   -- why it paused, etc.
    created_by  TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT,
    plan_json   TEXT NOT NULL           -- models + repeats, question ids, symmetry
);
CREATE TABLE IF NOT EXISTS asks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       INTEGER NOT NULL REFERENCES runs(id),
    seq          INTEGER NOT NULL,
    model        TEXT NOT NULL,
    qid          TEXT NOT NULL,
    question     TEXT NOT NULL,
    agent        TEXT NOT NULL,          -- primary | peer (settings.yaml agents)
    agent_name   TEXT NOT NULL,
    rep          INTEGER NOT NULL,
    status       TEXT NOT NULL,          -- pending | running | ok | error | skipped
    http_status  INTEGER,
    error        TEXT,
    tries        INTEGER DEFAULT 0,
    started_at   TEXT,
    finished_at  TEXT,
    wall_ms      REAL,
    response_z   BLOB,                   -- the full response incl. trace, zlib-compressed JSON
    {", ".join(f"{c} {'INTEGER' if c in _NUMERIC else 'REAL' if c.startswith(('ms_', 'cost')) else 'TEXT'}" for c in SCORE_COLUMNS)}
);
CREATE INDEX IF NOT EXISTS asks_run ON asks(run_id, status, seq);
CREATE INDEX IF NOT EXISTS asks_q ON asks(qid, fingerprint);
CREATE TABLE IF NOT EXISTS verdicts (
    qid         TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    verdict     TEXT NOT NULL,           -- correct | wrong
    note        TEXT,
    by_user     TEXT NOT NULL,
    at          TEXT NOT NULL,
    PRIMARY KEY (qid, fingerprint)
);
"""

_lock = threading.RLock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATABASE, check_same_thread=False, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


_con = _connect()
_con.executescript(_SCHEMA)


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    with _lock:
        try:
            yield _con
            _con.commit()
        except Exception:
            _con.rollback()
            raise


def rows(sql: str, args: tuple = ()) -> List[Dict[str, Any]]:
    with db() as con:
        return [dict(r) for r in con.execute(sql, args)]


def pack(response: Any) -> bytes:
    return zlib.compress(json.dumps(response, ensure_ascii=False).encode("utf-8"), 6)


def unpack(blob: Optional[bytes]) -> Any:
    return None if blob is None else json.loads(zlib.decompress(blob).decode("utf-8"))


# ── runs ─────────────────────────────────────────────────────────────────────

def create_run(label: str, user: str, plan: Dict[str, Any], asks: List[Dict[str, Any]]) -> int:
    with db() as con:
        active = con.execute("SELECT 1 FROM runs WHERE status IN ('running','queued') LIMIT 1").fetchone()
        cur = con.execute(
            "INSERT INTO runs (label, status, created_by, created_at, plan_json) VALUES (?,?,?,?,?)",
            (label, "queued" if active else "running", user, now(), json.dumps(plan)))
        run_id = cur.lastrowid
        con.executemany(
            "INSERT INTO asks (run_id, seq, model, qid, question, agent, agent_name, rep, status, "
            "expected_category, n_places, n_years, n_attributes) VALUES (?,?,?,?,?,?,?,?,'pending',?,?,?,?)",
            [(run_id, i, a["model"], a["qid"], a["question"], a["agent"], a["agent_name"], a["rep"],
              a["expected_category"], a["n_places"], a["n_years"], a["n_attributes"]) for i, a in enumerate(asks)])
        return run_id


def set_run(run_id: int, **fields: Any) -> None:
    with db() as con:
        con.execute(f"UPDATE runs SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?", (*fields.values(), run_id))


def get_run(run_id: int) -> Optional[Dict[str, Any]]:
    found = rows("SELECT * FROM runs WHERE id=?", (run_id,))
    return found[0] if found else None


def list_runs() -> List[Dict[str, Any]]:
    return rows("""
        SELECT r.*, COUNT(a.id) AS asks_total,
               SUM(a.status IN ('ok','error')) AS asks_done,
               SUM(a.status = 'error') AS asks_failed,
               SUM(a.status = 'skipped') AS asks_skipped,
               SUM(CASE WHEN a.status IN ('ok','error') THEN a.wall_ms END) AS ms_spent,
               SUM(a.cost_usd) AS cost_usd
        FROM runs r LEFT JOIN asks a ON a.run_id = r.id
        GROUP BY r.id ORDER BY r.id DESC""")


def next_active_run() -> Optional[Dict[str, Any]]:
    """The running run, or else the oldest queued one (which then starts)."""
    found = rows("SELECT * FROM runs WHERE status='running' ORDER BY id LIMIT 1")
    if found:
        return found[0]
    queued = rows("SELECT * FROM runs WHERE status='queued' ORDER BY id LIMIT 1")
    if queued:
        set_run(queued[0]["id"], status="running")
        return get_run(queued[0]["id"])
    return None


# ── asks ─────────────────────────────────────────────────────────────────────

def next_pending(run_id: int) -> Optional[Dict[str, Any]]:
    found = rows("SELECT * FROM asks WHERE run_id=? AND status='pending' ORDER BY seq LIMIT 1", (run_id,))
    return found[0] if found else None


def start_ask(ask_id: int) -> None:
    with db() as con:
        con.execute("UPDATE asks SET status='running', started_at=?, tries=tries+1 WHERE id=?", (now(), ask_id))


def finish_ask(ask_id: int, status: str, http_status: Optional[int], error: Optional[str],
               wall_ms: float, response: Any, scores: Dict[str, Any]) -> None:
    cols = {c: scores.get(c) for c in SCORE_COLUMNS if c in scores}
    with db() as con:
        con.execute(
            f"UPDATE asks SET status=?, http_status=?, error=?, finished_at=?, wall_ms=?, response_z=?"
            f"{''.join(f', {c}=?' for c in cols)} WHERE id=?",
            (status, http_status, error, now(), round(wall_ms, 1), None if response is None else pack(response),
             *cols.values(), ask_id))


def update_scores(ask_id: int, scores: Dict[str, Any]) -> None:
    cols = {c: scores.get(c) for c in SCORE_COLUMNS}
    with db() as con:
        con.execute(f"UPDATE asks SET {', '.join(f'{c}=?' for c in cols)} WHERE id=?", (*cols.values(), ask_id))


def requeue_interrupted() -> int:
    """Asks that were in flight when the evaluator stopped go back in the queue."""
    with db() as con:
        return con.execute("UPDATE asks SET status='pending' WHERE status='running'").rowcount


def get_ask(ask_id: int) -> Optional[Dict[str, Any]]:
    found = rows("SELECT * FROM asks WHERE id=?", (ask_id,))
    return found[0] if found else None


def asks_of(run_ids: List[int], with_response: bool = False) -> List[Dict[str, Any]]:
    cols = "*" if with_response else ", ".join(
        c for c in ["id", "run_id", "seq", "model", "qid", "question", "agent", "agent_name", "rep", "status",
                    "http_status", "error", "tries", "started_at", "finished_at", "wall_ms", *SCORE_COLUMNS])
    marks = ",".join("?" * len(run_ids))
    return rows(f"SELECT {cols} FROM asks WHERE run_id IN ({marks}) ORDER BY run_id, seq", tuple(run_ids))


# ── verdicts ─────────────────────────────────────────────────────────────────

def verdicts() -> Dict[tuple, Dict[str, Any]]:
    return {(v["qid"], v["fingerprint"]): v for v in rows("SELECT * FROM verdicts")}


def set_verdict(qid: str, fp: str, verdict: Optional[str], note: Optional[str], user: str) -> None:
    with db() as con:
        if verdict is None:
            con.execute("DELETE FROM verdicts WHERE qid=? AND fingerprint=?", (qid, fp))
        else:
            con.execute("INSERT INTO verdicts (qid, fingerprint, verdict, note, by_user, at) VALUES (?,?,?,?,?,?) "
                        "ON CONFLICT(qid, fingerprint) DO UPDATE SET verdict=excluded.verdict, note=excluded.note, "
                        "by_user=excluded.by_user, at=excluded.at", (qid, fp, verdict, note, user, now()))
