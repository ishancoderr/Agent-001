"""
The background worker: takes the next pending ask of the running run, sends
it to the agent, scores the answer and stores both. One ask at a time, so the
response times are not distorted by the evaluator's own load.

The worker asks as the user who started the run: it signs that user a
session with the agents' shared AUTH_SECRET (agent1/auth/session.py), so the
agents' logs show who ran the evaluation, and a run of many hours does not
depend on the browser session that started it.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

import httpx

from agent1.auth.session import COOKIE_NAME, encode, issue

from . import store
from .config import AGENTS, RETRIES, TIMEOUT_S
from .question_set import run_questions
from .scoring import score

log = logging.getLogger("evaluator.runner")


class AgentDown(Exception):
    """The agent could not be reached even after the retries."""


def session_cookie(username: str) -> Dict[str, str]:
    return {COOKIE_NAME: encode(issue(username, f"{username} (evaluation)"))}


def agent_get(role: str, path: str, username: str) -> Any:
    r = httpx.get(AGENTS[role]["url"] + path, cookies=session_cookie(username), timeout=30)
    r.raise_for_status()
    return r.json()


def ask_agent(role: str, question: str, model: str, username: str,
              should_stop) -> Tuple[Optional[int], Optional[Dict[str, Any]], Optional[str], float, int]:
    """(http status, response, error, ms, tries). Retries what settings.yaml
    `retries` calls transient; raises AgentDown if the agent stays unreachable."""
    url = AGENTS[role]["url"] + "/query"
    body = {"query": question, "llm": model, "trace": True}
    waits = list(RETRIES["backoff_s"])
    attempts = int(RETRIES["attempts"])
    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        try:
            r = httpx.post(url, json=body, cookies=session_cookie(username), timeout=TIMEOUT_S)
            ms = (time.perf_counter() - started) * 1000
            if r.status_code in RETRIES["on_status"] and attempt < attempts:
                log.warning("%s answered %s — retrying", AGENTS[role]["name"], r.status_code)
            else:
                try:
                    data = r.json()
                except ValueError:
                    data = None
                error = None if r.status_code == 200 else str((data or {}).get("detail") or r.text[:500])
                return r.status_code, (data if r.status_code == 200 else None), error, ms, attempt
        except httpx.TimeoutException as exc:
            return None, None, f"timed out after {TIMEOUT_S:.0f} s ({type(exc).__name__})", \
                (time.perf_counter() - started) * 1000, attempt
        except httpx.TransportError as exc:
            if attempt == attempts:
                raise AgentDown(f"{AGENTS[role]['name']} is not reachable at {AGENTS[role]['url']}: {exc}") from exc
            log.warning("%s not reachable (%s) — retrying", AGENTS[role]["name"], exc)
        wait = waits[min(attempt - 1, len(waits) - 1)] if waits else 10
        for _ in range(int(wait)):
            if should_stop():
                raise AgentDown("paused while waiting to retry")
            time.sleep(1)
    raise AssertionError("unreachable")


class Worker(threading.Thread):
    def __init__(self) -> None:
        super().__init__(name="evaluator-worker", daemon=True)
        self.wake = threading.Event()
        self.current: Optional[Dict[str, Any]] = None       # the ask being answered, for the UI

    def poke(self) -> None:
        self.wake.set()

    def run(self) -> None:
        while True:
            try:
                if not self._step():
                    self.wake.wait(5)
                    self.wake.clear()
            except Exception:                                   # noqa: BLE001 — never let the worker die
                log.exception("evaluator worker error")
                time.sleep(5)

    def _step(self) -> bool:
        run = store.next_active_run()
        if run is None:
            return False
        if run["started_at"] is None:
            store.set_run(run["id"], started_at=store.now())
        ask = store.next_pending(run["id"])
        if ask is None:
            store.set_run(run["id"], status="done", finished_at=store.now(), note=None)
            log.info("run %s finished", run["id"])
            return True
        self._answer(run, ask)
        return True

    def _answer(self, run: Dict[str, Any], ask: Dict[str, Any]) -> None:
        q = run_questions(json.loads(run["plan_json"])).get(ask["qid"])
        store.start_ask(ask["id"])
        self.current = {**ask, "since": time.time()}
        def paused() -> bool:
            return (store.get_run(run["id"]) or {}).get("status") != "running"

        try:
            status, response, error, ms, tries = ask_agent(
                ask["agent"], ask["question"], ask["model"], run["created_by"], paused)
        except AgentDown as exc:
            with store.db() as con:
                con.execute("UPDATE asks SET status='pending' WHERE id=?", (ask["id"],))
            if store.get_run(run["id"])["status"] == "running":
                store.set_run(run["id"], status="paused", note=str(exc))
                log.error("run %s paused: %s", run["id"], exc)
            return
        finally:
            self.current = None
        scores = score(q, ask["model"], response, status) if q else {"answer_summary": "question not in the key"}
        store.finish_ask(ask["id"], "ok" if status == 200 else "error", status, error, ms, response, scores)
        with store.db() as con:
            con.execute("UPDATE asks SET tries=? WHERE id=?", (tries, ask["id"]))
        log.info("run %s · %s · %s · %s rep %s → %s %s (%.1f s)", run["id"], ask["model"], ask["agent_name"],
                 ask["qid"], ask["rep"], status, scores.get("answer_summary", "")[:80], ms / 1000)
