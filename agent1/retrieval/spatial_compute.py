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

from ..pipeline.gazetteer import entity_type_of, names_of, normalize_entity_name
from ..pipeline.prompt_loader import CATEGORY_CANDIDATE_TYPES
from ..messaging.agent_registry import AGENT_NAME, PRIMARY_PEER
from ..pipeline.query_params import (DEFAULT_ENTITY_TYPE, DEFAULT_ZONE_TARGET, ENTITY_SRID,
                                     UNLISTED_NAME_DEFAULT, QueryParams, entity_label)
from ..settings import (DEFAULT_DISTANCE_KM, DIRECTION_SEARCH_RADIUS_KM, DIRECTION_SECTORS,
                        PLACE_REFERENCE_KINDS, relationship_kind, relationship_wording, sector_bounds)
from .gap_detector import Exchange, Shape, ask_peer, get_shapes, _peer
from .sql_writer import write_and_run

log = logging.getLogger("agent1.retrieval.spatial_compute")

# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_OPERATION — Scenarios 13-16
# ═══════════════════════════════════════════════════════════════════════════

def run_operation(params: QueryParams, queries: List[str], exchange: Exchange) -> Dict[str, Any]:
    """Get both (or all) input shapes, check their SRIDs agree, then run the
    operation as one LLM-written statement. Union over more than two shapes
    is a fold (Scenario 13). BufferWithin tests named targets against a zone
    around the first name. Returns {"shapes", "missing", "result"}; result is
    None when an input is held by neither agent. When the question also asks
    what lies inside the new shape (params.target_entity, a zone-searchable
    type from entities.yaml), "matches" holds {"local", "remote"} — ours and
    the ones Agent-2 found."""
    operation = params.operation
    names = params.spatial
    if operation == "BufferWithin":
        entities = [(n, entity_type_of(n, UNLISTED_NAME_DEFAULT if i == 0 else params.entity_type or DEFAULT_ENTITY_TYPE))
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
        dist_m = (params.distance_km or DEFAULT_DISTANCE_KM) * 1000
        rows = write_and_run(
            params.raw_query, "SPATIAL_OPERATION", "buffer_within",
            shown={"operation": operation, "spatial": names, "distance_km": params.distance_km},
            bind={"ref_wkt": ref.wkt, "ref_srid": ref.srid, "dist_m": dist_m,
                  "names": [t.entity_name for t in targets], "wkts": [t.wkt for t in targets],
                  "cand_srid": targets[0].srid},          # SRIDs agree, checked above
            required=["entity_name", "meets_zone"], queries=queries, label="named targets within a zone",
        )
        out["result"] = {"reference": ref.entity_name, "distance_km": params.distance_km or DEFAULT_DISTANCE_KM,
                         "targets": [{"name": r["entity_name"], "meets_zone": r["meets_zone"]} for r in rows]}
        return out

    result = ordered[0]
    for nxt in ordered[1:] if operation == "Union" else ordered[1:2]:
        wkt = write_and_run(
            operation_question(operation), "SPATIAL_OPERATION", "compute",
            shown={"operation": operation, "spatial": names},
            bind={"wkt_a": result.wkt, "srid_a": result.srid, "wkt_b": nxt.wkt, "srid_b": nxt.srid},
            required=["wkt"], queries=queries, label=f"{operation} of two shapes",
        )[0]["wkt"]
        result = Shape("", result.entity_type, wkt, result.srid, source=AGENT_NAME)
    out["result"] = {"wkt": result.wkt, "srid": result.srid}

    if params.target_entity:
        # "...and which cities lie inside it?" The new shape is a zone like the
        # one Scenario 20 builds: test our own table of that type, then send
        # the zone to Agent-2 to test its own, excluding what we already found.
        target = params.target_entity
        local = entities_in_zone(zone_question(target), result.wkt, result.srid, [], queries, target)
        resp = ask_peer("zone", _peer().ask_within_zone, result.wkt, result.srid,
                          [m.entity_name for m in local], target, exchange=exchange)
        remote = [Shape(fg.spatial_entity, fg.entity_type, fg.geometry, fg.srid, source=PRIMARY_PEER)
                  for fg in resp.get("found", [])]
        out["matches"] = {"local": local, "remote": remote}
    return out


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_ADJACENCY / _DIRECTION / _DISTANCE — Scenarios 17-19
# ═══════════════════════════════════════════════════════════════════════════

def resolve_relationship(params: QueryParams, queries: List[str], exchange: Exchange) -> QueryParams:
    """Fill params.spatial with the candidates for which the relationship
    holds, plus params.verdict for a yes/no question and params.unknown_places
    for candidates whose shape neither agent holds. The candidate type is the
    category prompt's `candidate_entity:` (states, today).

    Shapes needed: a yes/no question ("Do Bayern and Sachsen touch?") needs
    only the subject and the reference (Scenario 17); a set question
    ("Which states border Thüringen?") needs every candidate. A distance is
    measured from any named place, so its reference is fetched as its own type."""
    rel = params.spatial_relationship
    if rel is None or not rel.refs:
        raise ValueError(f"{params.query_type} needs a reference place, but none was extracted.")
    if params.query_type == "SPATIAL_DISTANCE" and rel.distance_km is None:
        raise ValueError("SPATIAL_DISTANCE needs a distance, but none was extracted.")

    # The kinds this category may produce come from config/settings.yaml.
    kind = relationship_kind(params.query_type, rel.type)

    # Every member of the category's candidate type is tested ("which STATES
    # border X"); the type comes from the prompt's `candidate_entity:`, and a
    # follow-up attribute question fetches data for that same type.
    cand_type = CATEGORY_CANDIDATE_TYPES[params.query_type]
    params.entity_type = cand_type
    members = ([normalize_entity_name(rel.subject, cand_type)] if rel.subject else names_of(cand_type))
    refs = [(r, entity_type_of(r, UNLISTED_NAME_DEFAULT if kind in PLACE_REFERENCE_KINDS else cand_type))
            for r in rel.refs]
    candidates = [(m, cand_type) for m in members]
    needed = list(dict.fromkeys(candidates + refs))

    shapes, missing = get_shapes(needed, queries, exchange)
    unknown = sorted({name for (name, et) in missing if et == cand_type})
    params.unknown_places = unknown

    cand_shapes = [shapes[c] for c in candidates if c in shapes]
    # The model sees only the spatial part of the question. "Population in
    # 2019 of the states bordering X" would otherwise tempt it to fetch the
    # population here; that is the data path's job, after this step.
    wording = relationship_wording(kind, rel.distance_km)          # config/settings.yaml
    question = f"Which of the candidate {entity_label(cand_type)} {wording} {', '.join(rel.refs)}?"
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
                  "cand_srid": cand_shapes[0].srid if cand_shapes else ENTITY_SRID[cand_type],
                  "ref": ref_shape.entity_name, "ref_wkt": ref_shape.wkt, "ref_srid": ref_shape.srid,
                  "dist_m": (rel.distance_km or 0) * 1000,
                  # a direction's sector (settings.yaml direction_sectors), bound
                  "az_start": sector_bounds(kind)[0] if kind in DIRECTION_SECTORS else 0,
                  "az_end": sector_bounds(kind)[1] if kind in DIRECTION_SECTORS else 0},
            required=["entity_name"], queries=queries, label=f"{kind} test against {ref_shape.entity_name}",
            # the values this kind is decided by are given, never written in
            must_use=(["az_start", "az_end"] if kind in DIRECTION_SECTORS
                      else ["dist_m"] if kind in PLACE_REFERENCE_KINDS else []),
        )
        hits = [r["entity_name"] for r in rows]
        log.info("       | %s %s: %s", kind, ref_shape.entity_name, hits)
        qualifying = list(hits) if qualifying is None else [h for h in qualifying if h in set(hits)]

    params.spatial = list(qualifying or [])
    params.verdict = _verdict(rel.subject, params.spatial, unknown, qualifying is None, cand_type)
    if rel.subject:
        log.info("       | Verdict: %s %s %s -> %s", rel.subject, kind, rel.refs,
                 {True: "YES", False: "NO", None: "UNKNOWN"}[params.verdict])
    log.info("       | Resolved to %d %s: %s", len(params.spatial), entity_label(cand_type), params.spatial)
    return params


def _verdict(subject: Optional[str], qualifying: List[str], unknown: List[str],
             undetermined: bool, cand_type: str) -> Optional[bool]:
    """Yes/no for a question that named a subject, else None. A missing
    shape gives None, never False: not knowing whether two states touch is a
    different answer from knowing that they do not (Scenario 17)."""
    if not subject or undetermined:
        return None
    stored = normalize_entity_name(subject, cand_type)
    if stored in unknown:
        return None
    return stored in qualifying


# ═══════════════════════════════════════════════════════════════════════════
# SPATIAL_RELATIONSHIP_BUFFER — Scenario 20, query delegation
# ═══════════════════════════════════════════════════════════════════════════

def buffer_query(params: QueryParams, queries: List[str], exchange: Exchange) -> Dict[str, Any]:
    """Which members of a zone-searchable type (cities, today) lie within N km
    of a place, or inside the place itself when N is 0 ("cities in Hessen").
    The answer cannot be named in advance, so: get the reference shape
    (asking Agent-2 if needed), build the zone, test our own table, then send
    the zone itself to Agent-2 to test its own (achieve), excluding what we
    already have."""
    ref_name = params.spatial[0]
    direction = params.direction
    if direction:
        distance_km = params.distance_km          # None: as far as direction_search_radius_km
    else:
        distance_km = DEFAULT_DISTANCE_KM if params.distance_km is None else params.distance_km
    target = params.target_entity or DEFAULT_ZONE_TARGET
    ref_pair = (ref_name, entity_type_of(ref_name, UNLISTED_NAME_DEFAULT))

    shapes, _missing = get_shapes([ref_pair], queries, exchange)
    if ref_pair not in shapes:
        return {"reference": None, "local": [], "remote": [], "distance_km": distance_km,
                "direction": direction, "target_entity": target}
    ref = shapes[ref_pair]

    if direction:
        # A wedge from the place's centre between the sector's bearings
        # (settings.yaml direction_sectors), the place itself removed.
        radius_km = distance_km or DIRECTION_SEARCH_RADIUS_KM
        az_start, az_end = sector_bounds(direction)
        zone = write_and_run(
            params.raw_query, "SPATIAL_RELATIONSHIP_BUFFER", "sector",
            shown={"spatial": params.spatial, "direction": direction, "radius_km": radius_km},
            bind={"ref_wkt": ref.wkt, "ref_srid": ref.srid, "radius_m": radius_km * 1000,
                  "az_start": az_start, "az_end": az_end},
            required=["wkt", "srid"], queries=queries, label=f"area {direction} {ref.entity_name}",
        )[0]
    elif distance_km:
        zone = write_and_run(
            params.raw_query, "SPATIAL_RELATIONSHIP_BUFFER", "zone",
            shown={"spatial": params.spatial, "distance_km": distance_km},
            bind={"ref_wkt": ref.wkt, "ref_srid": ref.srid, "dist_m": distance_km * 1000},
            required=["wkt", "srid"], queries=queries, label=f"{distance_km:g} km zone around {ref.entity_name}",
        )[0]
    else:
        zone = {"wkt": ref.wkt, "srid": ref.srid}      # inside the place itself: its own shape is the zone
    zone_srid = zone["srid"] or ref.srid

    # The reference is left out of its own answer only when it is one of the
    # things searched for (Kassel near Kassel), not when it is the container
    # (the city of Berlin inside the state of Berlin).
    own = [ref.entity_name] if ref.entity_type == target else []
    local = entities_in_zone(zone_question(target), zone["wkt"], zone_srid, own, queries, target)
    exclude = own + [m.entity_name for m in local]
    resp = ask_peer("zone", _peer().ask_within_zone, zone["wkt"], zone_srid, exclude, target, exchange=exchange)
    remote = [Shape(fg.spatial_entity, fg.entity_type, fg.geometry, fg.srid, source=PRIMARY_PEER)
              for fg in resp.get("found", [])]
    return {"reference": ref, "local": local, "remote": remote, "distance_km": distance_km,
            "direction": direction, "target_entity": target}


def operation_question(operation: str) -> str:
    """The question the compute step is written for. Not the user's: a merge
    that also asks for data ("...and the total live births in 2019") would
    tempt the model to add the data to the shape's SQL; that data is fetched
    by its own step."""
    return f"{operation} of these two shapes"


def zone_question(entity_type: str) -> str:
    """The question the "within" step is written for. Deliberately not the
    user's: the zone already holds any distance, direction or merge the user
    asked for, and their wording ("north of Dortmund", "in Hessen") only
    tempts the model to apply it a second time instead of using :zone_wkt."""
    return f"Which of our {entity_label(entity_type)} lie inside this zone?"


def entities_in_zone(question: str, zone_wkt: str, zone_srid: int, exclude: List[str],
                     queries: List[str], entity_type: str) -> List[Shape]:
    """Our own members of `entity_type` inside a zone — the "within" step,
    used by both sides of Scenario 20 and by merge-then-search. Which table
    and how a member is tested (a point within, a line or area intersecting)
    come from entities.yaml through the SQL prompt's schema description."""
    rows = write_and_run(
        question, "SPATIAL_RELATIONSHIP_BUFFER", "within",
        shown={"target_entity": entity_type, "exclude": exclude},
        bind={"zone_wkt": zone_wkt, "zone_srid": zone_srid, "exclude": [e for e in exclude if e]},
        required=["entity_name", "wkt", "srid"], queries=queries,
        label=f"our {entity_label(entity_type)} inside the zone",
    )
    return [Shape(r["entity_name"], entity_type, r["wkt"], r["srid"] or zone_srid) for r in rows]


def zone_for_peer(wkt: str, srid: int, exclude: List[str], entity_type: str, asker: str) -> List[Dict[str, Any]]:
    """A peer (`asker`, the KQML sender) delegated a zone test to us: test our
    own members of `entity_type` (the type its request named), in wire form."""
    hits = entities_in_zone(f"{asker} asks which of our {entity_label(entity_type)} lie inside this zone",
                            wkt, srid, exclude, [], entity_type)
    return [{"spatial_entity": m.entity_name, "entity_type": entity_type, "geometry": m.wkt, "srid": m.srid}
            for m in hits]
