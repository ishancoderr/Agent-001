"""
POST /query   — user submits a natural-language geospatial query
GET  /health  — liveness probe
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from ..pipeline import run as run_pipeline
from ..messaging.agent_registry import AGENT_NAME, PRIMARY_PEER
from ..pipeline.query_params import DEFAULT_ENTITY_TYPE, RELATIONSHIP_TYPES, system_capabilities_description
from ..retrieval.gap_detector import Exchange, answer_query, get_shapes
from ..retrieval.spatial_compute import buffer_query, resolve_relationship, run_operation
from ..evaluation import log_evaluation_metrics
from kqml_messaging import response_status

log = logging.getLogger("agent1.controller.query")
router = APIRouter()

SEPARATOR = "_" * 60


class UserQuery(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    # Per-request override of the OpenAI model used for classification and
    # extraction. Omit to use CLASSIFY_MODEL/EXTRACT_MODEL from the server's
    # .env (see agent1/.env.example) — this is for a caller who wants a
    # specific model for one query, not for setting the deployment default.
    model: Optional[str] = Field(None, min_length=1, max_length=100)


class QueryInfo(BaseModel):
    raw: str
    type: str
    spatial: List[str]
    temporal: List[int]
    attributes: List[str]
    # Which entities.yaml entity type the rows in `data` are about. Each row
    # names its place in `spatial` (the KQML wire's own field name) whatever
    # the type, so a client reads this to label the column ("federal state",
    # "river") instead of assuming one type.
    entity_type: str


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
    records_local:   int
    records_peer:   int
    records_from_both:      int
    records_unavailable:    int


class Tokens(BaseModel):
    local: int
    peer: int
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
    log.info("         New user query received by %s", AGENT_NAME)
    log.info(SEPARATOR)
    log.info("       │ Request ID : %s", request_id)
    log.info("       │ Query      : %r", body.query)

    # ── Step 1: understand the question (clean, classify, extract params) ────
    log.info("STEP 1 │ Parsing natural-language query with GPT-4o mini ...")
    try:
        params = run_pipeline(body.query, model=body.model)
    except Exception as exc:
        log.error("STEP 1 │ FAILED – %s", exc)
        raise HTTPException(status_code=400, detail=f"Parse error: {exc}") from exc
    tokens_local = params.classify_tokens + params.extract_tokens

    log.info("STEP 1 │ Done")
    log.info("       │ Query type : %s", params.query_type)

    # ── Unrelated — reject before any DB lookup or KQML exchange ───────────────
    if params.query_type == "UNRELATED":
        return _handle_unrelated(params, body.query, request_id, timestamp, t0, tokens_local)

    # ── Data was asked for but no year was named or implied ────────────────────
    if params.query_type == "NEEDS_YEAR":
        return _handle_needs_year(params, body.query, request_id, timestamp, t0, tokens_local)

    # ── Geometry lookup — bypass demographics pipeline entirely ───────────────
    if params.query_type == "GEOMETRY_LOOKUP":
        return _handle_geometry(params, body.query, request_id, timestamp, t0, tokens_local)

    # ── Spatial operation (Scenarios 13-16, 20) — named entities, no data lookup
    if params.query_type == "SPATIAL_OPERATION":
        return _handle_spatial_operation(params, body.query, request_id, timestamp, t0, tokens_local)

    # ── Relationship buffer over an open target type (Scenario 21) ────────────
    if params.query_type == "SPATIAL_RELATIONSHIP_BUFFER":
        return _handle_relationship_buffer(params, body.query, request_id, timestamp, t0, tokens_local)

    log.info("       │ Spatial    : %s", params.spatial)
    log.info("       │ Temporal   : %s", params.temporal)
    log.info("       │ Attributes : %s", params.attributes)
    if params.spatial_relationship:
        rel = params.spatial_relationship
        log.info("       │ Relationship: type=%s  refs=%s  dist_km=%s",
                 rel.type, rel.refs, rel.distance_km)

    # ── Step 2: a relationship question first finds WHICH states qualify:
    # get the shapes it needs (asking Agent-2 for missing ones), then the
    # LLM-written relationship SQL (Scenarios 17-19) ────────────────────────────
    rel_queries: List[str] = []
    rel_exchange = Exchange()
    if params.query_type in RELATIONSHIP_TYPES:
        try:
            params = resolve_relationship(params, rel_queries, rel_exchange)
        except ValueError as exc:
            log.error("STEP 2 │ FAILED – %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        log.info("STEP 2 │ Resolved (%s): %s (%d matches)",
                 params.query_type, params.spatial, len(params.spatial))
    else:
        log.info("STEP 2 │ Skipped (DIRECT_LOOKUP – no spatial resolution needed)")

    # ── Pure spatial question — the query asked only WHICH states, not for data
    if params.query_type != "DIRECT_LOOKUP" and not params.attributes:
        t1 = time.perf_counter()
        matches = [] if params.spatial == ["all"] else list(params.spatial)
        status = response_status(has_found=bool(matches), has_missing=not matches)
        total_ms = (t1 - t0) * 1000

        log.info(SEPARATOR)
        log.info("DONE   │ [%s] %s (spatial-only) status=%s  matches=%d  %.0f ms",
                 request_id, params.query_type, status, len(matches), total_ms)
        log.info(SEPARATOR)

        log_evaluation_metrics({
            "request_id":        request_id,
            "timestamp":         timestamp,
            "query":             body.query,
            "query_type":        params.query_type,
            "classify_tokens":   params.classify_tokens,
            "extract_tokens":    params.extract_tokens,
            "classify_model":     params.classify_model,
            "extract_model":      params.extract_model,
            "extracted_data":    params.extracted_data,
            "local_resolution": {
                "resolution_method": f"LLM-written PostGIS relationship SQL ({params.query_type})",
                "candidate_type":    params.entity_type,
                "resolved":          matches,
                "unknown":           params.unknown_places,
                "sql_queries":       rel_queries,
            },
            "kqml_exchanges":    rel_exchange.messages,
            "phase1_ms":         total_ms,
            "phase2_ms":         0.0,
            "phase3_ms":         0.0,
            "total_ms":          total_ms,
            "tokens_local":     tokens_local,
            "tokens_peer":     rel_exchange.tokens_peer,
            "tokens_total":      tokens_local + rel_exchange.tokens_peer,
            "total_records":     len(matches),
            "total_data_points": len(matches),
            "present_data_points": len(matches),
            "missing_data_points": 0,
            "complete_records":  len(matches),
            "partial_records":   0,
            "empty_records":     0,
            "status":            status,
        })

        rel = params.spatial_relationship
        return {
            "request_id": request_id,
            "status":     status,
            "query": {
                "raw":  body.query,
                "type": params.query_type,
                "entity_type": params.entity_type,
                "relationship": {
                    "type":        rel.type if rel else None,
                    "subject":     rel.subject if rel else None,
                    "refs":        rel.refs if rel else [],
                    "distance_km": rel.distance_km if rel else None,
                },
            },
            # A question that named a subject asked a yes/no. `verdict` carries
            # it; `matches` still carries the set the verdict was read from, so
            # the answer can be checked. verdict is null both when the question
            # asked for the list rather than a verdict, and when the subject or
            # reference has no geometry anywhere - see `unknown` for the
            # latter: a null verdict with the subject listed there means the
            # relationship genuinely could not be tested, not "no".
            "verdict": params.verdict,
            "matches": matches,
            "unknown": params.unknown_places,
            "summary": {"total": len(matches), "verdict": params.verdict,
                       "unknown": len(params.unknown_places),
                       "kqml_turns": rel_exchange.kqml_turns},
            "performance": {
                "phase1_ms": round(total_ms, 1),
                "phase2_ms": 0.0,
                "phase3_ms": 0.0,
                "total_ms":  round(total_ms, 1),
                "tokens": {"local": tokens_local, "peer": rel_exchange.tokens_peer,
                           "total": tokens_local + rel_exchange.tokens_peer},
            },
        }

    # ── Steps 3-5: local lookup, KQML ask for gaps, merge — one call now,
    # in retrieval/gap_detector.py's answer_query() ───────────────────────────
    log.info("STEP 3-5 │ Resolving locally, asking %s for gaps, merging ...", PRIMARY_PEER)
    log.info("       │ Looking for %d place(s) × %d year(s) × attrs=%s",
             len(params.spatial), len(params.temporal), params.attributes)

    answered = answer_query(params)
    local_result   = answered.local_result
    merged         = answered.merged
    kqml_turns     = answered.kqml_turns + rel_exchange.kqml_turns
    tokens_peer  = answered.tokens_peer + rel_exchange.tokens_peer
    kqml_exchanges = rel_exchange.messages + answered.kqml_exchanges
    phase1_ms      = answered.phase1_ms
    phase2_ms      = answered.phase2_ms
    phase3_ms      = answered.phase3_ms

    log.info("STEP 3-5 │ Done")
    log.info("       │ Found locally : %d record(s)", len(local_result.found))
    log.info("       │ Gaps          : %d slot(s)", len(local_result.gaps))
    for i, gap in enumerate(local_result.gaps, 1):
        log.info("       │   Gap %d: spatial=%s  temporal=%s  attrs=%s",
                 i, gap.spatial, gap.temporal, gap.attributes)
    log.info("       │ KQML turns    : %d", kqml_turns)
    log.info("       │ Merged total  : %d record(s)", len(merged))

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
    from_local = from_peer = from_both = unavail = 0
    for r in merged:
        src = r.get("source", "")
        if src == AGENT_NAME:     from_local   += 1
        elif src == PRIMARY_PEER: from_peer   += 1
        elif "+" in src:        from_both += 1
        elif src == "missing":  unavail   += 1

    log.info("       │ Groups  : complete=%d  partial=%d  missing=%d",
             len(complete_rows), len(partial_rows), len(missing_rows))
    log.info("       │ Sources : A1=%d  A2=%d  both=%d  unavail=%d",
             from_local, from_peer, from_both, unavail)
    log.info("       │ Data completeness: %.1f%%  (%d / %d points)",
             completeness, present_pts, total_pts)

    # ── Final status ──────────────────────────────────────────────────────────
    status = response_status(has_found=present_pts > 0,
                             has_missing=len(complete_rows) != len(merged))

    total_ms = (time.perf_counter() - t0) * 1000

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] status=%s  complete=%d  partial=%d  missing=%d  %.0f ms",
             request_id, status, len(complete_rows), len(partial_rows), len(missing_rows), total_ms)
    log.info(SEPARATOR)

    # ── Evaluation metrics ────────────────────────────────────────────────────
    log_evaluation_metrics({
        "request_id":          request_id,
        "timestamp":           timestamp,
        "query":               body.query,
        "query_type":          params.query_type,
        "classify_tokens":     params.classify_tokens,
        "extract_tokens":      params.extract_tokens,
        "classify_model":     params.classify_model,
        "extract_model":      params.extract_model,
        "extracted_data":      params.extracted_data,
        "local_resolution": {
            "places_queried":     params.spatial,
            "found_locally":      len(local_result.found),
            "gaps_found":         len(local_result.gaps),
            "gap_detail":         [
                {"spatial": g.spatial, "temporal": g.temporal, "attributes": g.attributes}
                for g in local_result.gaps
            ],
            "gap_diagnosis":      local_result.diagnosis,
            "sql_queries":        rel_queries + local_result.queries,
        },
        "parsed_spatial":      params.spatial,
        "parsed_temporal":     params.temporal,
        "parsed_attributes":   params.attributes,
        "kqml_exchanges":      kqml_exchanges,
        "phase1_ms":           phase1_ms,
        "phase2_ms":           phase2_ms,
        "phase3_ms":           phase3_ms,
        "total_ms":            total_ms,
        "tokens_local":       tokens_local,
        "tokens_peer":       tokens_peer,
        "tokens_total":        tokens_local + tokens_peer,
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
            entity_type=params.entity_type or DEFAULT_ENTITY_TYPE,
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
            records_local=from_local,
            records_peer=from_peer,
            records_from_both=from_both,
            records_unavailable=unavail,
        ),
        performance=Performance(
            phase1_ms=round(phase1_ms, 1),
            phase2_ms=round(phase2_ms, 1),
            phase3_ms=round(phase3_ms, 1),
            total_ms=round(total_ms, 1),
            tokens=Tokens(
                local=tokens_local,
                peer=tokens_peer,
                total=tokens_local + tokens_peer,
            ),
        ),
    )


def _handle_unrelated(params, raw_query: str, request_id: str, timestamp: str, t0: float, tokens_local: int):
    """The query names no German state/city and asks for none of this system's
    data — nothing to look up locally, nothing to send the peer. Rejected outright
    rather than coerced into a meaningless DIRECT_LOOKUP."""
    total_ms = (time.perf_counter() - t0) * 1000

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] UNRELATED — rejected  %.0f ms", request_id, total_ms)
    log.info(SEPARATOR)

    log_evaluation_metrics({
        "request_id":        request_id,
        "timestamp":         timestamp,
        "query":             raw_query,
        "query_type":        "UNRELATED",
        "classify_tokens":   params.classify_tokens,
        "extract_tokens":    0,
        "classify_model":     params.classify_model,
        "extract_model":      params.extract_model,
        "extracted_data":    {},
        "local_resolution": {
            "note": "rejected before any local database lookup was attempted",
        },
        "kqml_exchanges":    [],
        "phase1_ms":         total_ms,
        "phase2_ms":         0.0,
        "phase3_ms":         0.0,
        "total_ms":          total_ms,
        "tokens_local":     tokens_local,
        "tokens_peer":     0,
        "tokens_total":      tokens_local,
        "total_records":     0,
        "total_data_points": 0,
        "present_data_points": 0,
        "missing_data_points": 0,
        "complete_records":  0,
        "partial_records":   0,
        "empty_records":     0,
        "status":            "rejected",
    })

    return {
        "request_id": request_id,
        "status":     "rejected",
        "message": system_capabilities_description(),
        "query": {"raw": raw_query, "type": "UNRELATED"},
        "performance": {
            "phase1_ms": round(total_ms, 1),
            "phase2_ms": 0.0,
            "phase3_ms": 0.0,
            "total_ms":  round(total_ms, 1),
            "tokens": {"local": tokens_local, "peer": 0, "total": tokens_local},
        },
    }


def _handle_needs_year(params, raw_query: str, request_id: str, timestamp: str, t0: float, tokens_local: int):
    """The query asked for data (population/marriages/live_births) but named
    or implied no year. Guessing one used to mean a question about 1985
    silently got answered with 2021's figures instead - a wrong answer with
    nothing disclosing the swap. Rejecting and saying exactly what is missing
    is the honest response, the same way an UNRELATED question is rejected
    rather than forced into a category it doesn't fit."""
    total_ms = (time.perf_counter() - t0) * 1000

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] NEEDS_YEAR — rejected  %.0f ms", request_id, total_ms)
    log.info(SEPARATOR)

    log_evaluation_metrics({
        "request_id":        request_id,
        "timestamp":         timestamp,
        "query":             raw_query,
        "query_type":        "NEEDS_YEAR",
        "classify_tokens":   params.classify_tokens,
        "extract_tokens":    params.extract_tokens,
        "classify_model":     params.classify_model,
        "extract_model":      params.extract_model,
        "extracted_data":    params.extracted_data,
        "local_resolution": {
            "note": "rejected before any local database lookup was attempted "
                    "- no year was named or implied",
        },
        "kqml_exchanges":    [],
        "phase1_ms":         total_ms,
        "phase2_ms":         0.0,
        "phase3_ms":         0.0,
        "total_ms":          total_ms,
        "tokens_local":     tokens_local,
        "tokens_peer":     0,
        "tokens_total":      tokens_local,
        "total_records":     0,
        "total_data_points": 0,
        "present_data_points": 0,
        "missing_data_points": 0,
        "complete_records":  0,
        "partial_records":   0,
        "empty_records":     0,
        "status":            "rejected",
    })

    return {
        "request_id": request_id,
        "status":     "rejected",
        "message": (
            f"This question asks for {', '.join(params.attributes)} but doesn't say "
            "which year. Add one to answer it, for example:\n"
            f"  - a specific year: \"...in 2021\"\n"
            f"  - a range: \"...from 2019 to 2023\"\n"
            f"  - a relative reference: \"...this year\" or \"...now\""
        ),
        "query": {"raw": raw_query, "type": "NEEDS_YEAR", "attributes": params.attributes},
        "performance": {
            "phase1_ms": round(total_ms, 1),
            "phase2_ms": 0.0,
            "phase3_ms": 0.0,
            "total_ms":  round(total_ms, 1),
            "tokens": {"local": tokens_local, "peer": 0, "total": tokens_local},
        },
    }


def _handle_geometry(params, raw_query: str, request_id: str,
                     timestamp: str, t0: float, tokens_local: int):
    """Handle GEOMETRY_LOOKUP queries — resolve locally then ask the peer if missing."""
    entities = params.entities or []
    if not entities:
        return {"request_id": request_id, "status": "error",
                "message": "No entities found in geometry query.",
                "performance": {"phase1_ms": round((time.perf_counter()-t0)*1000,1),
                                "phase2_ms":0,"phase3_ms":0,"total_ms":0,
                                "tokens":{"local":tokens_local,"peer":0,"total":tokens_local}}}
    log.info("GEOM   │ Resolving %d entity/entities: %s", len(entities), entities)

    # Scenarios 9-12: SqlWriter fetches our shapes, the gap (no row, or row
    # with a NULL shape) goes to Agent-2 in one :missing-geometries ask.
    sql_queries: List[str] = []
    exchange = Exchange()
    pairs = [(e["entity_name"], e["entity_type"]) for e in entities]
    shapes, still_missing = get_shapes(pairs, sql_queries, exchange)
    kqml_turns     = exchange.kqml_turns
    tokens_peer  = exchange.tokens_peer
    kqml_exchanges = exchange.messages

    geometries = []
    for pair in pairs:
        shape = shapes.get(pair)
        if shape is not None:
            geometries.append({"entity_name": shape.entity_name, "entity_type": shape.entity_type,
                               "wkt": shape.wkt, "srid": shape.srid, "source": shape.source})
        else:
            geometries.append({"entity_name": pair[0], "entity_type": pair[1], "wkt": None, "srid": None,
                               "source": "not_found", "miss_mode_local": still_missing.get(pair)})

    t3 = time.perf_counter()
    phase1_ms = exchange.local_ms
    phase2_ms = exchange.peer_ms
    total_ms  = (t3 - t0) * 1000
    phase3_ms = max(total_ms - phase1_ms - phase2_ms, 0.0)
    local_names = sorted(s.entity_name for s in shapes.values() if s.source == AGENT_NAME)
    missing_here = [name for (name, _t) in pairs if (name, _t) not in shapes or shapes[(name, _t)].source != AGENT_NAME]

    found_count   = sum(1 for g in geometries if g["wkt"] is not None)
    missing_count = len(geometries) - found_count

    status = response_status(has_found=found_count > 0, has_missing=missing_count > 0)

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] geometry status=%s  found=%d  missing=%d  %.0f ms",
             request_id, status, found_count, missing_count, total_ms)
    log.info(SEPARATOR)

    log_evaluation_metrics({
        "request_id":        request_id,
        "timestamp":         timestamp,
        "query":             raw_query,
        "query_type":        "GEOMETRY_LOOKUP",
        "classify_tokens":   params.classify_tokens,
        "extract_tokens":    params.extract_tokens,
        "classify_model":     params.classify_model,
        "extract_model":      params.extract_model,
        "extracted_data":    params.extracted_data,
        "local_resolution": {
            "entities_requested": [e["entity_name"] for e in entities],
            "found_locally":      local_names,
            "still_missing_after_local_db": missing_here,
            "sql_queries":        sql_queries,
        },
        "kqml_exchanges":    kqml_exchanges,
        "phase1_ms":         phase1_ms,
        "phase2_ms":         phase2_ms,
        "phase3_ms":         phase3_ms,
        "total_ms":          total_ms,
        "tokens_local":     tokens_local,
        "tokens_peer":     tokens_peer,
        "tokens_total":      tokens_local + tokens_peer,
        "total_records":     len(geometries),
        "total_data_points": len(geometries),
        "present_data_points": found_count,
        "missing_data_points": missing_count,
        "complete_records":  found_count,
        "partial_records":   0,
        "empty_records":     missing_count,
        "status":            status,
    })

    return {
        "request_id": request_id,
        "status":     status,
        "query": {
            "raw":      raw_query,
            "type":     "GEOMETRY_LOOKUP",
            "entities": entities,
        },
        "geometries": geometries,
        "summary": {
            "total":    len(geometries),
            "found":    found_count,
            "missing":  missing_count,
        },
        "performance": {
            "phase1_ms": round(phase1_ms, 1),
            "phase2_ms": round(phase2_ms, 1),
            "phase3_ms": round(phase3_ms, 1),
            "total_ms":  round(total_ms, 1),
            "tokens": {
                "local": tokens_local,
                "peer": tokens_peer,
                "total":   tokens_local + tokens_peer,
            },
        },
    }


def _wkt_geometry_type(wkt: str) -> str:
    """The leading word of a WKT string names its geometry type. A WKT string
    always carries this - it is not extra work to read it, only to bother
    checking - and it is the only way to tell a real overlap (POLYGON /
    MULTIPOLYGON) from two shapes that merely touch (LINESTRING) or a pair
    with no intersection at all (an empty collection). Two administrative
    states sharing only a border, per Scenario 14, produce exactly this: a
    geometrically correct result that is not an area, and looks identical to
    a real shared region unless this is read out."""
    if not wkt:
        return "EMPTY"
    return wkt.strip().split("(", 1)[0].strip().split()[0].upper()


_AREA_GEOMETRY_TYPES = {"POLYGON", "MULTIPOLYGON"}


def _handle_spatial_operation(params, raw_query: str, request_id: str,
                              timestamp: str, t0: float, tokens_local: int):
    """Scenarios 13-16 (Union/Intersection/Difference/SymDifference) and the
    named-target BufferWithin. Every input is named, so its shape is fetched
    like GEOMETRY_LOOKUP (locally, or via a :missing-geometries ask), the SRIDs
    are checked, and only then does the LLM-written operation SQL run here —
    the operation itself is never missing (Section 3.5), only an input can be."""
    operation = params.operation
    names     = params.spatial or []

    if not operation or len(names) < 2:
        return {"request_id": request_id, "status": "error",
                "message": "SPATIAL_OPERATION requires an operation and at least two named entities.",
                "performance": {"phase1_ms": round((time.perf_counter()-t0)*1000, 1),
                                "phase2_ms": 0, "phase3_ms": 0, "total_ms": 0,
                                "tokens": {"local": tokens_local, "peer": 0, "total": tokens_local}}}

    log.info("SPOP   │ Operation: %s  entities=%s", operation, names)

    sql_queries: List[str] = []
    exchange = Exchange()
    error: Optional[str] = None
    try:
        outcome = run_operation(params, sql_queries, exchange)
    except ValueError as exc:                   # SRID mismatch or unusable SQL — a real error, not a gap
        log.error("SPOP   │ Operation failed: %s", exc)
        outcome, error = {"shapes": {}, "missing": {}, "result": None}, str(exc)

    shapes, missing, result = outcome["shapes"], outcome["missing"], outcome["result"]
    sources = {s.entity_name: s.source for s in shapes.values()}
    unresolved = sorted({name for (name, _t) in missing})

    total_ms  = (time.perf_counter() - t0) * 1000
    phase1_ms = exchange.local_ms
    phase2_ms = exchange.peer_ms
    phase3_ms = max(total_ms - phase1_ms - phase2_ms, 0.0)

    if error:
        status = "error"
    elif result is None:
        status = response_status(has_found=False, has_missing=True)
    else:
        status = response_status(has_found=True, has_missing=False)

    payload: Dict[str, Any] = {}
    if result is not None and operation == "BufferWithin":
        payload = result
    elif result is not None:
        geometry_type = _wkt_geometry_type(result["wkt"])
        payload = {"result": {"wkt": result["wkt"], "srid": result["srid"], "geometry_type": geometry_type}}
        if operation == "Intersection":
            # Two neighbouring states meet along a line and share no area
            # (Scenario 14) — a correct, complete answer, spelled out here.
            has_area = geometry_type in _AREA_GEOMETRY_TYPES
            payload["result"]["has_shared_area"] = has_area
            if not has_area:
                payload["note"] = (
                    f"{names[0]} and {names[1]} share no area"
                    + (f" — they meet only along a boundary ({geometry_type})."
                       if geometry_type in ("LINESTRING", "MULTILINESTRING")
                       else " — their boundaries do not touch at all."
                       if geometry_type in ("GEOMETRYCOLLECTION", "EMPTY", "POINT", "MULTIPOINT")
                       else ".")
                )



    # "...and which cities lie inside it?" — same shape of answer as the
    # Scenario 20 zone search: ours and Agent-2's, each tagged with its source.
    found = outcome.get("matches")
    if found is not None:
        payload["matches"] = _zone_matches(found["local"] + found["remote"])
        payload["summary"] = {"total": len(payload["matches"]), "from_local": len(found["local"]),
                              "from_peer": len(found["remote"])}

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] SPATIAL_OPERATION op=%s status=%s  %.0f ms", request_id, operation, status, total_ms)
    log.info(SEPARATOR)

    found_count = len(names) - len(unresolved)
    log_evaluation_metrics({
        "request_id": request_id, "timestamp": timestamp, "query": raw_query,
        "query_type": "SPATIAL_OPERATION",
        "classify_tokens": params.classify_tokens, "extract_tokens": params.extract_tokens,
        "classify_model": params.classify_model, "extract_model": params.extract_model,
        "extracted_data": params.extracted_data,
        "local_resolution": {
            "operation":          operation,
            "entities_requested": names,
            "target_entity":      params.target_entity,
            "matches_found":      len(payload.get("matches", [])),
            "sources":            sources,
            "still_missing":      unresolved,
            "error":              error,
            "sql_queries":        sql_queries,
        },
        "kqml_exchanges": exchange.messages,
        "phase1_ms": phase1_ms, "phase2_ms": phase2_ms, "phase3_ms": phase3_ms, "total_ms": total_ms,
        "tokens_local": tokens_local, "tokens_peer": exchange.tokens_peer,
        "tokens_total": tokens_local + exchange.tokens_peer,
        "total_records": len(names), "total_data_points": len(names),
        "present_data_points": found_count, "missing_data_points": len(unresolved),
        "complete_records": found_count if result is not None else 0,
        "partial_records": 0, "empty_records": len(unresolved),
        "status": status,
    })

    response: Dict[str, Any] = {
        "request_id": request_id,
        "status":     status,
        "query": {"raw": raw_query, "type": "SPATIAL_OPERATION", "operation": operation,
                  "spatial": names, "target_entity": params.target_entity, "sources": sources},
        **payload,
        "performance": {
            "phase1_ms": round(phase1_ms, 1), "phase2_ms": round(phase2_ms, 1),
            "phase3_ms": round(phase3_ms, 1), "total_ms": round(total_ms, 1),
            "tokens": {"local": tokens_local, "peer": exchange.tokens_peer,
                       "total": tokens_local + exchange.tokens_peer},
        },
    }
    if unresolved:
        response["still_missing"] = unresolved
    if error:
        response["message"] = error
    return response


def _zone_matches(found) -> List[Dict[str, Any]]:
    """Places found inside a zone, in response form, sorted by name. Each
    carries its own entity_type, so the response never assumes cities."""
    return sorted(
        [{"name": m.entity_name, "entity_type": m.entity_type, "wkt": m.wkt, "srid": m.srid, "source": m.source}
         for m in found],
        key=lambda m: m["name"],
    )


def _handle_relationship_buffer(params, raw_query: str, request_id: str,
                                timestamp: str, t0: float, tokens_local: int):
    """Scenario 20: which members of a zone-searchable type (cities, today)
    lie within N km of a place. They are the answer, not the input, so they
    cannot be named in a request: the zone is built here, tested against our
    own table, then sent to the peer to test its own (query delegation)."""
    if not params.spatial:
        return {"request_id": request_id, "status": "error",
                "message": "No reference place found in the query.",
                "performance": {"phase1_ms": round((time.perf_counter()-t0)*1000, 1),
                                "phase2_ms": 0, "phase3_ms": 0, "total_ms": 0,
                                "tokens": {"local": tokens_local, "peer": 0, "total": tokens_local}}}

    log.info("SPOP   │ Buffer query: %s within %s km", params.spatial[0], params.distance_km)

    sql_queries: List[str] = []
    exchange = Exchange()
    outcome = buffer_query(params, sql_queries, exchange)
    ref, local, remote = outcome["reference"], outcome["local"], outcome["remote"]
    distance_km, target = outcome["distance_km"], outcome["target_entity"]
    matches = _zone_matches(local + remote)

    total_ms  = (time.perf_counter() - t0) * 1000
    phase1_ms = exchange.local_ms
    phase2_ms = exchange.peer_ms
    phase3_ms = max(total_ms - phase1_ms - phase2_ms, 0.0)

    if ref is None:
        log.warning("SPOP   │ Reference place %r held by neither agent — no zone can be built", params.spatial[0])
    status = response_status(has_found=bool(matches), has_missing=ref is None or not matches)

    log.info(SEPARATOR)
    log.info("DONE   │ [%s] buffer status=%s  found=%d  %.0f ms", request_id, status, len(matches), total_ms)
    log.info(SEPARATOR)

    log_evaluation_metrics({
        "request_id": request_id, "timestamp": timestamp, "query": raw_query,
        "query_type": "SPATIAL_RELATIONSHIP_BUFFER",
        "classify_tokens": params.classify_tokens, "extract_tokens": params.extract_tokens,
        "classify_model": params.classify_model, "extract_model": params.extract_model,
        "extracted_data": params.extracted_data,
        "local_resolution": {
            "reference":        ref.entity_name if ref else params.spatial[0],
            "reference_source": ref.source if ref else "not_found",
            "distance_km":      distance_km,
            "target_entity":    target,
            "local_catalogue_matches": len(local),
            "note": "the matches cannot be named in advance — the zone is built once, "
                    f"tested against this agent's table, then sent to {PRIMARY_PEER} to test its own",
            "sql_queries": sql_queries,
        },
        "kqml_exchanges": exchange.messages,
        "phase1_ms": phase1_ms, "phase2_ms": phase2_ms, "phase3_ms": phase3_ms, "total_ms": total_ms,
        "tokens_local": tokens_local, "tokens_peer": exchange.tokens_peer,
        "tokens_total": tokens_local + exchange.tokens_peer,
        "total_records": len(matches), "total_data_points": len(matches),
        "present_data_points": len(matches), "missing_data_points": 0,
        "complete_records": len(matches), "partial_records": 0, "empty_records": 0,
        "status": status,
    })

    return {
        "request_id": request_id,
        "status":     status,
        "query": {
            "raw":              raw_query,
            "type":             "SPATIAL_RELATIONSHIP_BUFFER",
            "reference":        ref.entity_name if ref else params.spatial[0],
            "reference_source": ref.source if ref else "not_found",
            "distance_km":      distance_km,
            "target_entity":    target,
        },
        "matches": matches,
        "summary": {"total": len(matches), "from_local": len(local), "from_peer": len(remote)},
        "performance": {
            "phase1_ms": round(phase1_ms, 1), "phase2_ms": round(phase2_ms, 1),
            "phase3_ms": round(phase3_ms, 1), "total_ms": round(total_ms, 1),
            "tokens": {"local": tokens_local, "peer": exchange.tokens_peer,
                       "total": tokens_local + exchange.tokens_peer},
        },
    }


@router.get("/health")
def health():
    log.info("Health check OK")
    return {"status": "ok", "agent": AGENT_NAME, "peers": [PRIMARY_PEER]}
