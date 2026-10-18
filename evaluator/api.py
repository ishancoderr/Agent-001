"""
The evaluator's HTTP API, used by the workbench's Evaluation tab. Every route
needs the workbench login (the agents' session cookie, checked with the same
AUTH_SECRET), except /health.
"""
from __future__ import annotations

import difflib
import io
import os
import threading
import json
import zipfile
import logging
from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from agent1.auth import AuthUser, require_user

from . import metrics, store
from .config import AGENTS, ESTIMATE, PRICING, SETTINGS, load_questions, repeats_for
from .runner import Worker, agent_get
from .question_set import Item, resolve, run_questions
from .scoring import _complexity, score

log = logging.getLogger("evaluator.api")
app = FastAPI(title="GeoQuery evaluator")
worker = Worker()


@app.on_event("startup")
def _start() -> None:
    n = store.requeue_interrupted()
    if not SETTINGS.get("resume_on_start", True):
        with store.db() as con:
            con.execute("UPDATE runs SET status='paused', note='evaluator restarted' WHERE status='running'")
    log.info("evaluator up (%d interrupted ask(s) requeued)", n)
    worker.start()


@app.get("/health")
def health():
    return {"status": "ok", "pid": os.getpid(), "agents": AGENTS}


@app.post("/shutdown")
def shutdown(user: AuthUser = Depends(require_user)):
    """Stop the evaluator (the tab's Stop button). An ask in flight is asked
    again on the next start; a running run carries on then."""
    log.info("evaluator stopped by %s", user.username)
    threading.Timer(0.5, os._exit, [0]).start()
    return {"stopping": True}


# ── setup ────────────────────────────────────────────────────────────────────

def _models(username: str) -> List[Dict[str, Any]]:
    """The agents' models (GET /llms), with whether each agent can use it.
    `peer_online` is False when the peer did not answer — then whether it has
    a model is unknown, which is not the same as "not configured"."""
    try:
        primary = agent_get("primary", "/llms", username)
    except Exception as exc:                                     # noqa: BLE001
        raise HTTPException(502, f"{AGENTS['primary']['name']} is not reachable: {exc}") from exc
    try:
        peer: Optional[Dict[str, bool]] = {m["id"]: m["available"]
                                           for m in agent_get("peer", "/llms", username)["models"]}
    except Exception:                                            # noqa: BLE001
        peer = None
    return [{**m, "peer_online": peer is not None, "available_peer": bool(peer and peer.get(m["id"])),
             "default_repeats": repeats_for(m["id"]), "priced": m["id"] in PRICING} for m in primary["models"]]


def _check(plan: "RunPlan", listed: List[Dict[str, Any]]) -> None:
    """Can every ticked model run — on the primary, and on the peer when the
    symmetry run is on? Asked live on every estimate and start."""
    models = {m["id"]: m for m in listed}
    peer = AGENTS["peer"]
    for m in plan.models:
        if m.id not in models:
            raise HTTPException(400, f"unknown model {m.id!r}")
        if not models[m.id]["available"]:
            raise HTTPException(400, f"{models[m.id]['label']} is not configured on {AGENTS['primary']['name']} "
                                     "(its credentials are missing from that agent's .env)")
    if plan.symmetry and plan.models and not listed[0]["peer_online"]:
        raise HTTPException(400, f"{peer['name']} is not running ({peer['url']}) — start it for the symmetry "
                                 "run, or untick symmetry")
    for m in plan.models:
        if plan.symmetry and not models[m.id]["available_peer"]:
            raise HTTPException(400, f"{models[m.id]['label']} is not configured on {peer['name']} (its "
                                     "credentials are missing from that agent's .env) — configure it, or untick symmetry")


@app.get("/setup")
def setup(user: AuthUser = Depends(require_user)):
    return {
        "agents": {role: a["name"] for role, a in AGENTS.items()},
        "models": _models(user.username),
        "symmetry": bool(SETTINGS.get("symmetry", True)),
        # The answer key, for "load the test set": the items carry only the
        # question and its id; the labels are taken from the key on the server.
        "test_set": [{"id": q["id"], "question": q["question"]} for q in load_questions()],
    }


class ModelPlan(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    repeats: int = Field(ge=1, le=20)


class RunPlan(BaseModel):
    """Step 1: the models (and repeats); step 2: the question set."""
    label: str = Field("", max_length=120)
    models: List[ModelPlan] = Field(min_length=1)
    items: List[Item] = Field(min_length=1, max_length=5000)
    symmetry: bool = True


def _expand(plan: RunPlan, models: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(questions, asks): the question set resolved against the ticked
    models, and every ask in the order they will run — model by model, per
    question the repeats on the primary agent, then the peer once."""
    ticked = [m.id for m in plan.models]
    questions = resolve(plan.items, models, ticked)
    asks = []
    for m in plan.models:
        for q in (q for q in questions if m.id in q["models"]):
            base = {"model": m.id, "qid": q["id"], "question": q["question"],
                    "expected_category": q["category"], **_complexity(q)}
            for rep in range(1, m.repeats + 1):
                asks.append({**base, "agent": "primary", "agent_name": AGENTS["primary"]["name"], "rep": rep})
            if plan.symmetry:
                asks.append({**base, "agent": "peer", "agent_name": AGENTS["peer"]["name"], "rep": 1})
    if not asks:
        raise HTTPException(400, "no question runs on a ticked model")
    return questions, asks


def _measured() -> Dict[str, Dict[str, float]]:
    """Each model's average tokens and seconds per ask so far, any run."""
    return {r["model"]: r for r in store.rows(
        "SELECT model, AVG(tokens_in) AS tin, AVG(tokens_out) AS tout, AVG(peer_tokens) AS tpeer, "
        "AVG(wall_ms) AS ms, COUNT(*) AS n FROM asks WHERE status='ok' GROUP BY model")}


@app.post("/estimate")
def estimate(plan: RunPlan, user: AuthUser = Depends(require_user)):
    models = _models(user.username)
    _check(plan, models)
    providers = {m["id"]: m["provider"] for m in models}
    measured = _measured()
    questions, asks = _expand(plan, models)
    out = []
    for m in plan.models:
        n = sum(a["model"] == m.id for a in asks)
        got = measured.get(m.id)
        if got and got["n"]:
            share = ESTIMATE["output_share"]
            tin, tout = got["tin"] + got["tpeer"] * (1 - share), got["tout"] + got["tpeer"] * share
            secs = got["ms"] / 1000
            basis = f"measured over {got['n']} ask(s)"
        else:
            total = ESTIMATE["tokens_per_ask"]
            tin, tout = total * (1 - ESTIMATE["output_share"]), total * ESTIMATE["output_share"]
            spa = ESTIMATE["seconds_per_ask"]
            secs = (spa.get("per_provider") or {}).get(providers.get(m.id, ""), spa["default"])
            basis = "default estimate (settings.yaml)"
        price = PRICING.get(m.id)
        cost = round(n * (tin * price["input"] + tout * price["output"]) / 1e6, 2) if price else None
        out.append({"model": m.id, "asks": n, "tokens": round(n * (tin + tout)), "cost_usd": cost,
                    "seconds": round(n * secs), "basis": basis})
    return {"asks": len(asks), "questions": len(questions), "models": out,
            "cost_usd": round(sum(o["cost_usd"] or 0 for o in out), 2),
            "seconds": sum(o["seconds"] for o in out)}


@app.post("/runs")
def create_run(plan: RunPlan, user: AuthUser = Depends(require_user)):
    listed = _models(user.username)
    models = {m["id"]: m for m in listed}
    _check(plan, listed)
    questions, asks = _expand(plan, listed)
    label = plan.label.strip() or ", ".join(models[m.id]["label"] for m in plan.models)
    stored = {"label": label, "models": [m.model_dump() for m in plan.models], "symmetry": plan.symmetry,
              "resolved": questions}
    run_id = store.create_run(label, user.username, stored, asks)
    worker.poke()
    return _run_detail(run_id)


# ── runs ─────────────────────────────────────────────────────────────────────

def _eta(run: Dict[str, Any]) -> Optional[float]:
    """Seconds left: each model's remaining asks × its measured time per ask."""
    left = store.rows("SELECT model, COUNT(*) AS n FROM asks WHERE run_id=? AND status IN ('pending','running') "
                      "GROUP BY model", (run["id"],))
    if not left:
        return 0.0
    measured = _measured()
    secs = 0.0
    for row in left:
        got = measured.get(row["model"])
        secs += row["n"] * ((got["ms"] / 1000) if got and got["ms"] else ESTIMATE["seconds_per_ask"]["default"])
    return round(secs)


def _plan_summary(plan_json: str) -> Dict[str, Any]:
    """The plan without its question list — just how many questions."""
    plan = json.loads(plan_json)
    resolved = plan.pop("resolved", None)
    if resolved is not None:
        plan["questions"] = len(resolved)
    elif isinstance(plan.get("questions"), list):
        plan["questions"] = len(plan["questions"])
    return plan


def _run_detail(run_id: int) -> Dict[str, Any]:
    run = next((r for r in store.list_runs() if r["id"] == run_id), None)
    if run is None:
        raise HTTPException(404, "no such run")
    run["plan"] = _plan_summary(run.pop("plan_json"))
    run["eta_s"] = _eta(run) if run["status"] in ("running", "queued", "paused") else None
    run["per_model"] = store.rows(
        "SELECT model, COUNT(*) AS total, SUM(status IN ('ok','error')) AS done, SUM(status='error') AS failed "
        "FROM asks WHERE run_id=? GROUP BY model ORDER BY MIN(seq)", (run_id,))
    cur = worker.current
    run["current"] = ({k: cur[k] for k in ("model", "qid", "question", "agent_name", "rep", "since")}
                      if cur and cur["run_id"] == run_id else None)
    return run


@app.get("/runs")
def list_runs(user: AuthUser = Depends(require_user)):
    out = []
    for r in store.list_runs():
        r["plan"] = _plan_summary(r.pop("plan_json"))
        out.append(r)
    return out


@app.get("/runs/{run_id}")
def get_run(run_id: int, user: AuthUser = Depends(require_user)):
    return _run_detail(run_id)


@app.post("/runs/{run_id}/rescore")
def rescore(run_id: int, user: AuthUser = Depends(require_user)):
    """Score the stored responses again with the current rules and answer key
    (after an edit to test_set_v2.yaml or settings.yaml) — no new asks."""
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(404, "no such run")
    key = run_questions(json.loads(run["plan_json"]))
    n = 0
    for a in store.asks_of([run_id], with_response=True):
        if a["status"] in ("ok", "error") and a["qid"] in key:
            store.update_scores(a["id"], score(key[a["qid"]], a["model"], store.unpack(a["response_z"]),
                                               a["http_status"]))
            n += 1
    return {"rescored": n}


@app.post("/runs/{run_id}/{action}")
def control(run_id: int, action: Literal["pause", "resume", "cancel"], user: AuthUser = Depends(require_user)):
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(404, "no such run")
    if action == "pause" and run["status"] in ("running", "queued"):
        store.set_run(run_id, status="paused", note=f"paused by {user.username}")
    elif action == "resume" and run["status"] == "paused":
        busy = store.rows("SELECT 1 FROM runs WHERE status='running' AND id<>?", (run_id,))
        store.set_run(run_id, status="queued" if busy else "running", note=None)
    elif action == "cancel" and run["status"] in ("running", "queued", "paused"):
        with store.db() as con:
            con.execute("UPDATE asks SET status='skipped' WHERE run_id=? AND status='pending'", (run_id,))
        store.set_run(run_id, status="cancelled", finished_at=store.now(), note=f"cancelled by {user.username}")
    else:
        raise HTTPException(409, f"cannot {action} a run that is {run['status']}")
    worker.poke()
    return _run_detail(run_id)


def _run_ids(runs: Optional[str]) -> List[int]:
    if not runs:
        return [r["id"] for r in store.list_runs()]
    try:
        return [int(x) for x in runs.split(",") if x.strip()]
    except ValueError as exc:
        raise HTTPException(400, "runs must be a comma-separated list of run ids") from exc


@app.get("/results")
def results(runs: Optional[str] = None, user: AuthUser = Depends(require_user)):
    asks = metrics.load(_run_ids(runs))
    return {"models": metrics.per_model(asks), "categories": metrics.per_category(asks),
            "questions": metrics.per_question(asks)}


@app.get("/asks")
def list_asks(runs: Optional[str] = None, qid: Optional[str] = None, model: Optional[str] = None,
              user: AuthUser = Depends(require_user)):
    asks = metrics.load(_run_ids(runs))
    asks = [a for a in asks if (qid is None or a["qid"] == qid) and (model is None or a["model"] == model)]
    for a in asks:
        a.pop("answer_view", None)
    return asks


@app.get("/asks/{ask_id}")
def get_ask(ask_id: int, user: AuthUser = Depends(require_user)):
    a = store.get_ask(ask_id)
    if a is None:
        raise HTTPException(404, "no such ask")
    a["response"] = store.unpack(a.pop("response_z"))
    a["answer_view"] = json.loads(a["answer_view"]) if a.get("answer_view") else None
    return a


# ── the hand-confirmed verdicts ──────────────────────────────────────────────

@app.get("/review")
def review(runs: Optional[str] = None, only_open: bool = True, user: AuthUser = Depends(require_user)):
    """Each distinct answer per question, with the asks that gave it — the
    list to confirm by hand. A verdict applies to that answer wherever it occurs."""
    verdicts = store.verdicts()
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for a in metrics.load(_run_ids(runs)):
        if a["status"] == "ok" and a.get("fingerprint"):
            groups[(a["qid"], a["fingerprint"])].append(a)
    views = {k: v[0]["answer_view"] for k, v in groups.items()}
    correct = defaultdict(list)
    for (qid, fp), v in verdicts.items():
        if v["verdict"] == "correct" and (qid, fp) in views:
            correct[qid].append(fp)
    order: Dict[str, int] = {}
    for a in metrics.load(_run_ids(runs)):
        order.setdefault(a["qid"], a["seq"] + a["run_id"] * 1_000_000)
    out = []
    for (qid, fp), asks in sorted(groups.items(), key=lambda kv: (order.get(kv[0][0], 1e9), -len(kv[1]))):
        v = verdicts.get((qid, fp))
        if only_open and v:
            continue
        view = json.loads(views[(qid, fp)])
        item = {
            "qid": qid, "question": asks[0]["question"], "expected_category": asks[0]["expected_category"],
            "fingerprint": fp, "summary": asks[0]["answer_summary"], "view": view,
            "asks": len(asks), "ask_ids": [a["id"] for a in asks][:50],
            "models": sorted({a["model"] for a in asks}), "agents": sorted({a["agent_name"] for a in asks}),
            "verdict": v["verdict"] if v else None, "note": v["note"] if v else None,
            "by_user": v["by_user"] if v else None,
            "suggestion": None, "diff_to_confirmed": None,
        }
        refs = [r for r in correct[qid] if r != fp]
        if not v:
            item["suggestion"] = "differs from the confirmed answer" if refs else "no confirmed answer yet"
        if refs:
            ref = json.dumps(json.loads(views[(qid, refs[0])]), indent=1, ensure_ascii=False).splitlines()
            mine = json.dumps(view, indent=1, ensure_ascii=False).splitlines()
            item["diff_to_confirmed"] = "\n".join(difflib.unified_diff(ref, mine, "confirmed", "this answer",
                                                                       n=1, lineterm=""))[:20000]
        out.append(item)
    return out


class VerdictBody(BaseModel):
    qid: str = Field(min_length=1, max_length=32)
    fingerprint: str = Field(min_length=1, max_length=64)
    verdict: Optional[Literal["correct", "wrong"]] = None    # None removes it
    note: Optional[str] = Field(None, max_length=1000)


@app.put("/verdicts")
def put_verdict(body: VerdictBody, user: AuthUser = Depends(require_user)):
    store.set_verdict(body.qid, body.fingerprint, body.verdict, body.note, user.username)
    return {"ok": True}


# ── CSV downloads ────────────────────────────────────────────────────────────

def _tag(runs: Optional[str], ids: List[int]) -> str:
    return "all-runs" if not runs else "runs-" + "-".join(map(str, ids))


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


@app.get("/export/model/{model}.csv")
def export_model(model: str, runs: Optional[str] = Query(None), user: AuthUser = Depends(require_user)):
    """One model's file: every ask of that model, with its question's
    consistency and symmetry on each row."""
    ids = _run_ids(runs)
    body = metrics.to_csv(metrics.model_file(metrics.load(ids), model), metrics.MODEL_FILE_COLUMNS)
    return Response(body, media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="evaluation_{_safe(model)}_{_tag(runs, ids)}.csv"'})


@app.get("/export/per-model.zip")
def export_per_model(runs: Optional[str] = Query(None), user: AuthUser = Depends(require_user)):
    """Every model's file in one download, plus the summary per model."""
    ids = _run_ids(runs)
    asks = metrics.load(ids)
    tag = _tag(runs, ids)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for model in dict.fromkeys(a["model"] for a in asks):
            z.writestr(f"evaluation_{_safe(model)}_{tag}.csv",
                       metrics.to_csv(metrics.model_file(asks, model), metrics.MODEL_FILE_COLUMNS))
        z.writestr(f"evaluation_summary_per_model_{tag}.csv", metrics.to_csv(metrics.per_model(asks)))
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="evaluation_per_model_{tag}.zip"'})


@app.get("/export/{kind}.csv")
def export(kind: Literal["asks", "questions", "models", "categories", "steps", "verdicts"],
           runs: Optional[str] = Query(None), user: AuthUser = Depends(require_user)):
    ids = _run_ids(runs)
    if kind == "steps":
        body = metrics.to_csv(metrics.steps(ids))
    elif kind == "verdicts":
        texts = {}
        for a in metrics.load(ids):
            texts.setdefault((a["qid"], a.get("fingerprint")), (a["question"], a["answer_summary"]))
        body = metrics.to_csv([{**v, "question": texts.get((v["qid"], v["fingerprint"]), ("", ""))[0],
                                "answer_summary": texts.get((v["qid"], v["fingerprint"]), ("", ""))[1]}
                               for v in store.verdicts().values()],
                              ["qid", "question", "fingerprint", "verdict", "note", "answer_summary", "by_user", "at"])
    else:
        asks = metrics.load(ids)
        rows = {"asks": lambda: asks, "questions": lambda: metrics.per_question(asks),
                "models": lambda: metrics.per_model(asks), "categories": lambda: metrics.per_category(asks)}[kind]()
        body = metrics.to_csv(rows, metrics.ASK_COLUMNS if kind == "asks" else None)
    tag = _tag(runs, ids)
    return Response(body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="evaluation_{kind}_{tag}.csv"'})
