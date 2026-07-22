"""
POST /query   — user submits a natural-language geospatial query
GET  /health  — liveness probe
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
import time as _time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..pipeline import parse_query, validate_spatial
from ..retrieval import execute_local_lookup
from ..retrieval.geometry_resolver import resolve_geometries
from ..messaging import send_kqml_ask
from ..messaging.kqml_geometry_client import send_kqml_geometry_ask
from ..result import merge_results
from ..evaluation import log_evaluation_metrics
from kqml_messaging import MessageFactory

log = logging.getLogger("agent1.controller.query")
router = APIRouter()

SEPARATOR = "_" * 60


class UserQuery(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)


class QueryInfo(BaseModel):
    raw: str
    type: str
    spatial: List[str]
    temporal: List[int]
    attributes: List[str]


class DataGroups(BaseModel):
    complete: List[Dict[str, Any]]
    partial:  List[Dict[str, Any]]
    missing:  List[Dict[str, Any]]


class Summary(BaseModel):
    total_records:       int
    complete_records:    int
    partial_records:     int
    missing_records:     int
    total_data_points:   int
    present_data_points: int
    missing_data_points: int
    completeness_pct:    float


class Provenance(BaseModel):
    kqml_turns:             int
    records_from_agent_1:   int
    records_from_agent_2:   int
    records_from_both:      int
    records_unavailable:    int


class Tokens(BaseModel):
    agent_1: int
    agent_2: int
    total:   int


class Performance(BaseModel):
    phase1_ms: float
    phase2_ms: float
    phase3_ms: float
    total_ms:  float
    tokens:    Tokens


class QueryResponse(BaseModel):
    request_id:  str
    status:      str
    query:       QueryInfo
    data:        DataGroups
    summary:     Summary
    provenance:  Provenance
    performance: Performance


@router.post("/query")
def handle_query(body: UserQuery):
    t0 = time.perf_counter()
    request_id = uuid.uuid4().hex[:8]
    timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log.info(SEPARATOR)
    log.info("                       START")
    log.info("         New user query received by Agent 1")
    log.info(SEPARATOR)
    log.info("       │ Request ID : %s", request_id)
    log.info("       │ Query      : %r", body.query)

    # ── Step 1: Parse NL query ─────────────────────────────────────────────────
    log.info("STEP 1 │ Parsing natural-language query with GPT-4o mini ...")
    try:
        params, tokens_agent1 = parse_query(body.query)
    except Exception as exc:
        log.error("STEP 1 │ FAILED – %s", exc)
        raise HTTPException(status_code=400, detail=f"Parse error: {exc}") from exc

    log.info("STEP 1 │ Done")
    log.info("       │ Query type : %s", params.query_type)

    # ── Geometry lookup — bypass demographics pipeline entirely ───────────────
    if params.query_type == "GEOMETRY_LOOKUP":
        return _handle_geometry(params, body.query, request_id, timestamp, t0, tokens_agent1)

    log.info("       │ Spatial    : %s", params.spatial)
    log.info("       │ Temporal   : %s", params.temporal)
    log.info("       │ Attributes : %s", params.attributes)
    if params.spatial_relationship:
        rel = params.spatial_relationship
        log.info("       │ Relationship: type=%s  refs=%s  dist_km=%s",
                 rel.type, rel.refs, rel.distance_km)

    # ── Step 2: Resolve spatial relationships ──────────────────────────────────
    if params.query_type != "DIRECT_LOOKUP":
        log.info("STEP 2 │ Resolving spatial relationship via PostGIS (%s) ...",
                 params.query_type)
        before = list(params.spatial)
        params = validate_spatial(params)
        log.info("STEP 2 │ Done")
        log.info("       │ Before  : %s", before)
        log.info("       │ Resolved: %s (%d states)", params.spatial, len(params.spatial))
    else:
        log.info("STEP 2 │ Skipped (DIRECT_LOOKUP – no spatial resolution needed)")

    # ── Step 3: Local database lookup ─────────────────────────────────────────
    log.info("STEP 3 │ Querying Agent-1 local database ...")
    log.info("       │ Looking for %d state(s) × %d year(s) × attrs=%s",
             len(params.spatial), len(params.temporal), params.attributes)

    local_result = execute_local_lookup(params)

    log.info("STEP 3 │ Done")
    log.info("       │ Found    : %d record(s)", len(local_result.found))
    log.info("       │ Gaps     : %d slot(s)", len(local_result.gaps))
    for i, gap in enumerate(local_result.gaps, 1):
        log.info("       │   Gap %d: spatial=%s  temporal=%s  attrs=%s",
                 i, gap.spatial, gap.temporal, gap.attributes)

    t1 = time.perf_counter()  # end of phase 1

    kqml_turns    = 0
    tokens_agent2 = 0
    agent2_data: List[Dict] = []

    # ── Step 4: KQML ask to Agent 2 (with retry) ─────────────────────────────
    if local_result.gaps:
        log.info("STEP 4 │ Gaps detected – sending KQML ask to Agent-2 ...")
        log.info("       │ Missing slots to send: %d", len(local_result.gaps))
        for attempt in range(1, 4):
            try:
                resp          = send_kqml_ask(local_result.gaps)
                kqml_turns    = 1
                agent2_data   = resp.get("found", [])
                tokens_agent2 = resp.get("tokens_agent2", 0)
                log.info("STEP 4 │ KQML tell received from Agent-2 (attempt %d)", attempt)
                log.info("       │ Agent-2 found   : %d record(s)", len(agent2_data))
                break
            except Exception as exc:
                log.warning("STEP 4 │ Agent-2 attempt %d failed – %s", attempt, exc)
                if attempt < 3:
                    _time.sleep(1.0 * attempt)
                else:
                    log.warning("STEP 4 │ Agent-2 unreachable after 3 attempts – gaps unresolved")
    else:
        log.info("STEP 4 │ Skipped (no gaps – Agent-2 not needed)")

    t2 = time.perf_counter()  # end of phase 2

    # ── Step 5: Merge results ─────────────────────────────────────────────────
    log.info("STEP 5 │ Merging results ...")
    merged = merge_results(
        local_result.found,
        agent2_data,
        requested_states=params.spatial,
        requested_years=params.temporal,
        requested_attrs=params.attributes,
    )
    log.info("STEP 5 │ Done – %d total records", len(merged))

    t3 = time.perf_counter()  # end of phase 3

    # ── Split into three groups ───────────────────────────────────────────────
    attrs = params.attributes
    complete_rows: List[Dict] = []
    partial_rows:  List[Dict] = []
    missing_rows:  List[Dict] = []
    present_pts = 0

    for row in merged:
        n = sum(1 for a in attrs if row.get(a) is not None)
        present_pts += n
        if n == len(attrs):
            complete_rows.append(row)
        elif n == 0:
            missing_rows.append(row)
        else:
            partial_rows.append(row)

    total_pts   = len(merged) * len(attrs)
    missing_pts = total_pts - present_pts
    completeness = round(present_pts / total_pts * 100, 1) if total_pts else 0.0

    # ── Provenance counts — single pass ──────────────────────────────────────
    from_a1 = from_a2 = from_both = unavail = 0
    for r in merged:
        src = r.get("source", "")
        if src == "Agent-1":    from_a1   += 1
        elif src == "Agent-2":  from_a2   += 1
        elif "+" in src:        from_both += 1
        elif src == "missing":  unavail   += 1

    log.info("       │ Groups  : complete=%d  partial=%d  missing=%d",
             len(complete_rows), len(partial_rows), len(missing_rows))
    log.info("       │ Sources : A1=%d  A2=%d  both=%d  unavail=%d",
             from_a1, from_a2, from_both, unavail)
    log.info("       │ Data completeness: %.1f%%  (%d / %d points)",
             completeness, present_pts, total_pts)

    # ── Final status ──────────────────────────────────────────────────────────
    if len(complete_rows) == len(merged):
        status = "complete"
    elif present_pts == 0:
        status = "not_found"
    else:
        status = "partial"

    phase1_ms = (t1 - t0) * 1000
    phase2_ms = (t2 - t1) * 1000
    phase3_ms = (t3 - t2) * 1000
    total_ms  = (t3 - t0) * 1000

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] status=%s  complete=%d  partial=%d  missing=%d  %.0f ms",
             request_id, status, len(complete_rows), len(partial_rows), len(missing_rows), total_ms)
    log.info(SEPARATOR)

    # ── Evaluation metrics ────────────────────────────────────────────────────
    log_evaluation_metrics({
        "request_id":          request_id,
        "timestamp":           timestamp,
        "query":               body.query,
        "phase1_ms":           phase1_ms,
        "phase2_ms":           phase2_ms,
        "phase3_ms":           phase3_ms,
        "total_ms":            total_ms,
        "tokens_agent1":       tokens_agent1,
        "tokens_agent2":       tokens_agent2,
        "tokens_total":        tokens_agent1 + tokens_agent2,
        "total_records":       len(merged),
        "total_data_points":   total_pts,
        "present_data_points": present_pts,
        "missing_data_points": missing_pts,
        "complete_records":    len(complete_rows),
        "partial_records":     len(partial_rows),
        "empty_records":       len(missing_rows),
        "status":              status,
    })

    return QueryResponse(
        request_id=request_id,
        status=status,
        query=QueryInfo(
            raw=body.query,
            type=params.query_type,
            spatial=params.spatial,
            temporal=params.temporal,
            attributes=params.attributes,
        ),
        data=DataGroups(
            complete=complete_rows,
            partial=partial_rows,
            missing=missing_rows,
        ),
        summary=Summary(
            total_records=len(merged),
            complete_records=len(complete_rows),
            partial_records=len(partial_rows),
            missing_records=len(missing_rows),
            total_data_points=total_pts,
            present_data_points=present_pts,
            missing_data_points=missing_pts,
            completeness_pct=completeness,
        ),
        provenance=Provenance(
            kqml_turns=kqml_turns,
            records_from_agent_1=from_a1,
            records_from_agent_2=from_a2,
            records_from_both=from_both,
            records_unavailable=unavail,
        ),
        performance=Performance(
            phase1_ms=round(phase1_ms, 1),
            phase2_ms=round(phase2_ms, 1),
            phase3_ms=round(phase3_ms, 1),
            total_ms=round(total_ms, 1),
            tokens=Tokens(
                agent_1=tokens_agent1,
                agent_2=tokens_agent2,
                total=tokens_agent1 + tokens_agent2,
            ),
        ),
    )


def _handle_geometry(params, raw_query: str, request_id: str,
                     timestamp: str, t0: float, tokens_agent1: int):
    """Handle GEOMETRY_LOOKUP queries — resolve locally then ask Agent-2 if missing."""
    entity_name = params.entity_name or ""
    entity_type = params.entity_type or "city"

    log.info("GEOM   │ Resolving geometry for %s (%s)", entity_name, entity_type)

    slot = MessageFactory.missing_geometry_slot(
        spatial_entity=entity_name,
        entity_type=entity_type,
    )

    # Try local DB first
    found_local, still_missing = resolve_geometries([slot])

    t1 = time.perf_counter()

    # Ask Agent-2 for anything not found locally
    found_remote = []
    kqml_turns   = 0
    tokens_agent2 = 0
    if still_missing:
        log.info("GEOM   │ Not found locally — asking Agent-2 ...")
        try:
            resp          = send_kqml_geometry_ask(still_missing)
            found_remote  = resp.get("found", [])
            kqml_turns    = 1
            log.info("GEOM   │ Agent-2 returned %d geometry result(s)", len(found_remote))
        except Exception as exc:
            log.warning("GEOM   │ Agent-2 unreachable — %s", exc)

    t2 = time.perf_counter()

    all_found = found_local + found_remote
    phase1_ms = (t1 - t0) * 1000
    phase2_ms = (t2 - t1) * 1000
    total_ms  = (t2 - t0) * 1000

    if all_found:
        fg = all_found[0]
        source = "Agent-1" if found_local else "Agent-2"
        log.info("GEOM   │ Resolved from %s: wkt=%.80s…", source, fg.geometry)
        result = {
            "entity_name": fg.spatial_entity,
            "entity_type": fg.entity_type,
            "wkt":         fg.geometry,
            "srid":        fg.srid,
            "source":      source,
        }
        status = "found"
    else:
        log.warning("GEOM   │ Geometry not found in either agent for %s (%s)", entity_name, entity_type)
        result = None
        status = "not_found"

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] geometry status=%s  %.0f ms", request_id, status, total_ms)
    log.info(SEPARATOR)

    return {
        "request_id":  request_id,
        "status":      status,
        "query": {
            "raw":         raw_query,
            "type":        "GEOMETRY_LOOKUP",
            "entity_name": entity_name,
            "entity_type": entity_type,
        },
        "geometry": result,
        "performance": {
            "phase1_ms": round(phase1_ms, 1),
            "phase2_ms": round(phase2_ms, 1),
            "phase3_ms": 0.0,
            "total_ms":  round(total_ms, 1),
            "tokens": {
                "agent_1": tokens_agent1,
                "agent_2": tokens_agent2,
                "total":   tokens_agent1 + tokens_agent2,
            },
        },
    }


@router.get("/health")
def health():
    log.info("Health check OK")
    return {"status": "ok", "agent": "Agent-1"}
