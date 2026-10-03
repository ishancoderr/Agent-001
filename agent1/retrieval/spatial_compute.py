"""
The spatial questions: get every shape a question needs (gap_detector.get_shapes,
which asks Agent-2 for whatever is missing), then let SqlWriter write the one
statement that computes the answer.

    run_operation()          SPATIAL_OPERATION, Scenarios 13-16 (+ named-target buffer)
    resolve_relationship()   SPATIAL_ADJACENCY / _DIRECTION / _DISTANCE, Scenarios 17-19
    buffer_query()           SPATIAL_RELATIONSHIP_BUFFER, Scenario 20 (query delegation)
    zone_for_peer()          Agent-2 delegates a zone test to us (Scenario 20, other side)

An operation or relationship is never missing — both agents run the same
code — only an input shape can be (Section 3.5). So a missing input blocks
the computation instead of producing a partial answer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from kqml_messaging import check_srid_agreement

from ..pipeline.gazetteer import GERMAN_STATES, normalize_entity_name
from ..pipeline.query_params import DEFAULT_ENTITY_TYPE, QueryParams
from .gap_detector import Exchange, Shape, ask_agent2, get_shapes, _peer
from .sql_writer import write_and_run

log = logging.getLogger("agent1.retrieval.spatial_compute")


def _entity_type_for(name: str, default: str) -> str:
    """A state if the name is one of the sixteen, otherwise `default`."""
    return "state" if normalize_entity_name(name, "state") in GERMAN_STATES else default


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_OPERATION — Scenarios 13-16
# ═══════════════════════════════════════════════════════════════════════════

def run_operation(params: QueryParams, queries: List[str], exchange: Exchange) -> Dict[str, Any]:
    """Get both (or all) input shapes, check their SRIDs agree, then run the
    operation as one LLM-written statement. Union over more than two shapes
    is a fold (Scenario 13). BufferWithin tests named targets against a zone
    around the first name. Returns {"shapes", "missing", "result"}; result is
    None when an input is held by neither agent."""
    operation = params.operation
    names = params.spatial
    if operation == "BufferWithin":
        entities = [(n, _entity_type_for(n, "city" if i == 0 else params.entity_type or DEFAULT_ENTITY_TYPE))
                    for i, n in enumerate(names)]
    else:
        entity_type = params.entity_type or DEFAULT_ENTITY_TYPE
        entities = [(n, entity_type) for n in names]

    shapes, missing = get_shapes(entities, queries, exchange)
    out: Dict[str, Any] = {"shapes": shapes, "missing": missing, "result": None}
    if missing:
        log.warning("       | Operation blocked, input held by neither agent: %s", sorted(missing))
        return out

    ordered = [shapes[pair] for pair in entities]
    for shape in ordered[1:]:
        check_srid_agreement(ordered[0].srid, shape.srid)     # Section 3: checked before it runs

    if operation == "BufferWithin":
        ref, targets = ordered[0], ordered[1:]
        dist_m = (params.distance_km or 100.0) * 1000
        rows = write_and_run(
            params.raw_query, "SPATIAL_OPERATION", "buffer_within",
            shown={"operation": operation, "spatial": names, "distance_km": params.distance_km},
            bind={"ref_wkt": ref.wkt, "ref_srid": ref.srid, "dist_m": dist_m,
                  "names": [t.entity_name for t in targets], "wkts": [t.wkt for t in targets]},
            required=["entity_name", "meets_zone"], queries=queries, label="named targets within a zone",
        )
        out["result"] = {"reference": ref.entity_name, "distance_km": params.distance_km or 100.0,
                         "targets": [{"name": r["entity_name"], "meets_zone": r["meets_zone"]} for r in rows]}
        return out

    result = ordered[0]
    for nxt in ordered[1:] if operation == "Union" else ordered[1:2]:
        wkt = write_and_run(
            params.raw_query, "SPATIAL_OPERATION", "compute",
            shown={"operation": operation, "spatial": names},
            bind={"wkt_a": result.wkt, "srid_a": result.srid, "wkt_b": nxt.wkt, "srid_b": nxt.srid},
            required=["wkt"], queries=queries, label=f"{operation} of two shapes",
        )[0]["wkt"]
        result = Shape("", result.entity_type, wkt, result.srid, source="Agent-1")
    out["result"] = {"wkt": result.wkt, "srid": result.srid}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_ADJACENCY / _DIRECTION / _DISTANCE — Scenarios 17-19
# ═══════════════════════════════════════════════════════════════════════════

def resolve_relationship(params: QueryParams, queries: List[str], exchange: Exchange) -> QueryParams:
    """Fill params.spatial with the states for which the relationship holds,
    plus params.verdict for a yes/no question and params.unknown_states for
    states whose shape neither agent holds.

    Shapes needed: a yes/no question ("Do Bayern and Sachsen touch?") needs
    only the subject and the reference (Scenario 17); a set question
    ("Which states border Thüringen?") needs every state. A distance is
    measured from a city or a state, so its reference is fetched as one."""
    rel = params.spatial_relationship
    if rel is None or not rel.refs:
        raise ValueError(f"{params.query_type} needs a reference place, but none was extracted.")
    if params.query_type == "SPATIAL_DISTANCE" and rel.distance_km is None:
        raise ValueError("SPATIAL_DISTANCE needs a distance, but none was extracted.")

    kind = {"SPATIAL_ADJACENCY": "adjacency", "SPATIAL_DISTANCE": "distance"}.get(params.query_type, rel.type)
    if kind not in {"adjacency", "distance", "north_of", "south_of", "east_of", "west_of"}:
        kind = "north_of"

    states = ([normalize_entity_name(rel.subject, "state")] if rel.subject else list(GERMAN_STATES))
    refs = [(r, _entity_type_for(r, "city") if kind == "distance" else "state") for r in rel.refs]
    candidates = [(s, "state") for s in states]
    needed = list(dict.fromkeys(candidates + refs))

    shapes, missing = get_shapes(needed, queries, exchange)
    unknown = sorted({name for (name, et) in missing if et == "state"})
    params.unknown_states = unknown

    cand_shapes = [shapes[c] for c in candidates if c in shapes]
    # The model sees only the spatial part of the question. "Population in
    # 2019 of the states bordering X" would otherwise tempt it to fetch the
    # population here; that is the data path's job, after this step.
    wording = {"adjacency": "border", "distance": f"lie within {rel.distance_km} km of"}.get(
        kind, f"lie {kind.replace('_of', '')} of")
    question = f"Which of the candidate states {wording} {', '.join(rel.refs)}?"
    qualifying: Optional[set] = None
    for ref in refs:
        if ref not in shapes:
            log.warning("       | Reference %s held by neither agent - relationship undetermined", ref[0])
            qualifying = None
            break
        ref_shape = shapes[ref]
        rows = write_and_run(
            question, "SPATIAL_RELATIONSHIP", "compute",
            shown={"spatial_relationship": {"type": kind, "refs": rel.refs, "subject": rel.subject,
                                            "distance_km": rel.distance_km}},
            bind={"names": [s.entity_name for s in cand_shapes], "wkts": [s.wkt for s in cand_shapes],
                  "ref": ref_shape.entity_name, "ref_wkt": ref_shape.wkt, "ref_srid": ref_shape.srid,
                  "dist_m": (rel.distance_km or 0) * 1000},
            required=["entity_name"], queries=queries, label=f"{kind} test against {ref_shape.entity_name}",
        )
        hits = [r["entity_name"] for r in rows]
        log.info("       | %s %s: %s", kind, ref_shape.entity_name, hits)
        qualifying = list(hits) if qualifying is None else [h for h in qualifying if h in set(hits)]

    params.spatial = list(qualifying or [])
    params.verdict = _verdict(rel.subject, params.spatial, unknown, qualifying is None)
    if rel.subject:
        log.info("       | Verdict: %s %s %s -> %s", rel.subject, kind, rel.refs,
                 {True: "YES", False: "NO", None: "UNKNOWN"}[params.verdict])
    log.info("       | Resolved to %d state(s): %s", len(params.spatial), params.spatial)
    return params


def _verdict(subject: Optional[str], qualifying: List[str], unknown: List[str],
             undetermined: bool) -> Optional[bool]:
    """Yes/no for a question that named a subject, else None. A missing
    shape gives None, never False: not knowing whether two states touch is a
    different answer from knowing that they do not (Scenario 17)."""
    if not subject or undetermined:
        return None
    stored = normalize_entity_name(subject, "state")
    if stored in unknown:
        return None
    return stored in qualifying


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_RELATIONSHIP_BUFFER — Scenario 20, query delegation
# ═══════════════════════════════════════════════════════════════════════════

def buffer_query(params: QueryParams, queries: List[str], exchange: Exchange) -> Dict[str, Any]:
    """Which cities lie within N km of a city. The answer cannot be named in
    advance, so: get the reference point (asking Agent-2 if needed), build
    the zone, test our own cities, then send the zone itself to Agent-2 to
    test its cities (achieve), excluding what we already have."""
    ref_name = params.spatial[0]
    distance_km = params.distance_km or 100.0
    ref_pair = (ref_name, "city")

    shapes, _missing = get_shapes([ref_pair], queries, exchange)
    if ref_pair not in shapes:
        return {"reference": None, "local": [], "remote": [], "distance_km": distance_km}
    ref = shapes[ref_pair]

    zone = write_and_run(
        params.raw_query, "SPATIAL_RELATIONSHIP_BUFFER", "zone",
        shown={"spatial": params.spatial, "distance_km": distance_km},
        bind={"ref_wkt": ref.wkt, "ref_srid": ref.srid, "dist_m": distance_km * 1000},
        required=["wkt", "srid"], queries=queries, label=f"{distance_km:g} km zone around {ref.entity_name}",
    )[0]
    zone_srid = zone["srid"] or ref.srid

    local = cities_in_zone(params.raw_query, zone["wkt"], zone_srid, [ref.entity_name], queries)
    exclude = [ref.entity_name] + [c.entity_name for c in local]
    resp = ask_agent2("zone", _peer().ask_within_zone, zone["wkt"], zone_srid, exclude, exchange=exchange)
    remote = [Shape(fg.spatial_entity, fg.entity_type, fg.geometry, fg.srid, source="Agent-2")
              for fg in resp.get("found", [])]
    return {"reference": ref, "local": local, "remote": remote, "distance_km": distance_km}


def cities_in_zone(question: str, zone_wkt: str, zone_srid: int, exclude: List[str],
                   queries: List[str]) -> List[Shape]:
    """Our own cities inside a zone (the "within" step, both sides of Scenario 20)."""
    rows = write_and_run(
        question, "SPATIAL_RELATIONSHIP_BUFFER", "within",
        shown={"target_entity": "city", "exclude": exclude},
        bind={"zone_wkt": zone_wkt, "zone_srid": zone_srid, "exclude": [e for e in exclude if e]},
        required=["entity_name", "wkt", "srid"], queries=queries, label="our cities inside the zone",
    )
    return [Shape(r["entity_name"], "city", r["wkt"], r["srid"] or zone_srid) for r in rows]


def zone_for_peer(wkt: str, srid: int, exclude: List[str]) -> List[Dict[str, Any]]:
    """Agent-2 delegated a zone test to us: test our cities, in wire form."""
    hits = cities_in_zone("Agent-2 asks which of our cities lie inside this zone",
                          wkt, srid, exclude, [])
    return [{"spatial_entity": c.entity_name, "entity_type": "city", "geometry": c.wkt, "srid": c.srid}
            for c in hits]
