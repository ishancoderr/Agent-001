"""
Start the evaluator from the workbench (its Evaluation tab's "Start
evaluator" button), so it doesn't need a terminal of its own.

The evaluator (`python -m evaluator`, the folder named in config/settings.yaml
`evaluator.module`) ships only with the agent whose repository holds it; on
the other agent /evaluator/status says "not installed" and the button stays
hidden. It is started as a separate, detached process: it keeps running when
this agent reloads or stops, and a run it was doing continues on the next start.
Stopping goes to the evaluator itself (its /shutdown).
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict

import httpx
import yaml
from fastapi import APIRouter, Depends, HTTPException

from ..auth import AuthUser, require_user
from ..messaging.agent_registry import AGENT_NAME
from ..settings import EVALUATOR

log = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluator", tags=["evaluator"])

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / EVALUATOR["module"]


def _installed() -> bool:
    return (PACKAGE / "__main__.py").exists()


def _url() -> str:
    """Where the evaluator listens: its own settings.yaml, or EVALUATOR_HOST /
    EVALUATOR_PORT — the same lookup as evaluator/config.py."""
    own = yaml.safe_load((PACKAGE / "settings.yaml").read_text(encoding="utf-8"))
    host = os.getenv("EVALUATOR_HOST") or own.get("host", "127.0.0.1")
    port = os.getenv("EVALUATOR_PORT") or own["port"]
    return f"http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}"


def _running() -> Dict[str, Any] | None:
    try:
        r = httpx.get(_url() + "/health", timeout=2)
        return r.json() if r.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        return None


def _status() -> Dict[str, Any]:
    if not _installed():
        return {"installed": False, "running": False, "agent": AGENT_NAME}
    health = _running()
    return {"installed": True, "running": health is not None, "agent": AGENT_NAME,
            "pid": (health or {}).get("pid"), "log": str(PACKAGE / "data" / "evaluator.log")}


@router.get("/status")
def status(user: AuthUser = Depends(require_user)):
    return _status()


_starting = threading.Lock()        # two clicks at once start one evaluator


def _spawn(command: list, env: Dict[str, str], out) -> subprocess.Popen:
    """A process that outlives this agent. On Windows it must also leave the
    job object the venv launcher runs this agent in — that job is closed, with
    everything in it, when uvicorn --reload restarts the agent."""
    common = dict(cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    if os.name != "nt":
        return subprocess.Popen(command, start_new_session=True, **common)
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP   # no console, no Ctrl+C
    try:
        return subprocess.Popen(command, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB, **common)
    except OSError:                     # a job that forbids breaking away: start inside it
        log.warning("EVAL   │ could not start the evaluator outside this agent's job — "
                    "it will stop when this agent restarts")
        return subprocess.Popen(command, creationflags=flags, **common)


@router.post("/start")
def start(user: AuthUser = Depends(require_user)):
    if not _installed():
        raise HTTPException(404, f"The evaluator is not part of {AGENT_NAME}")
    with _starting:
        return _start(user)


def _start(user: AuthUser) -> Dict[str, Any]:
    if _running():
        return _status()
    logs = PACKAGE / "data"
    logs.mkdir(parents=True, exist_ok=True)
    out = open(logs / "evaluator.log", "ab")
    env = {**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    proc = _spawn([sys.executable, "-X", "utf8", "-m", EVALUATOR["module"]], env, out)
    out.close()
    log.info("EVAL   │ %s started the evaluator (pid %s)", user.username, proc.pid)
    deadline = time.monotonic() + float(EVALUATOR["start_timeout_s"])
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise HTTPException(500, f"The evaluator stopped right away (exit code {proc.returncode}) — "
                                     f"see {logs / 'evaluator.log'}")
        if _running():
            return _status()
        time.sleep(0.5)
    raise HTTPException(504, f"The evaluator did not answer within {EVALUATOR['start_timeout_s']} s — "
                             f"see {logs / 'evaluator.log'}")
