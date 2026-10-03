"""
Get our own data, find what is missing, ask Agent-2, merge.

The same five steps run for every question, after parameter extraction:

    1. SqlWriter writes the SELECT from the question + parameters
    2. run it on this agent's database
    3. gap = what was asked for − what came back          (plain set arithmetic)
    4. ask Agent-2 for the gap over KQML (up to 3 tries)
    5. merge both agents' answers

Two kinds of thing can be missing, and both are handled here:

    values   (state, year, attribute) slots — Scenarios 1-8
             gap = Q \\ D1, classified per slot as spatial / temporal /
             thematic, giving the gap signature (S, T, A) of Section 1.5
    shapes   the geometry of a named place — Scenarios 9-12, and the inputs
             of every operation / relationship / buffer (13-20)
             gap = G' \\ H1, each with a miss mode: unknown-feature (no row)
             or geometry-null (row exists, shape empty), Section 2.3

The functions at the bottom answer Agent-2's own asks with the same fetches.
Gap detection is never routed through an LLM: every requested item is either
in the result or it is not.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from kqml_messaging import MessageFactory, gap_signature

from ..pipeline.gazetteer import GERMAN_STATES, normalize_entity_name
from ..pipeline.query_params import DEFAULT_ENTITY_TYPE, QueryParams
from .sql_writer import write_and_run

log = logging.getLogger("agent1.retrieval.gap_detector")


# ═══════════════════════════════════════════════════════════════════════════
# Data shapes
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DataRecord:
    """One place's values for one year, and which agent they came from."""
    state: str
    year: int
    values: Dict[str, Any] = field(default_factory=dict)
    source: str = "Agent-1"


@dataclass
class GapSlot:
    """A block of values this agent could not fill: places × years × attributes.
    `entity_type` travels on the wire so the peer knows which table to read."""
    spatial: List[str]
    temporal: List[int]
    attributes: List[str]
    entity_type: str = ""


@dataclass
class LocalResult:
    """What this agent found, what it is missing, why, and the SQL it ran."""
    found: List[DataRecord] = field(default_factory=list)
    gaps: List[GapSlot] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    # missing_spatial / missing_temporal / missing_attribute and the gap
    # signature (S, T, A) — local diagnosis only, never sent (Scenario 4).
    diagnosis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnsweredQuery:
    """The merged answer to a data question, plus timing and the exchange."""
    merged: List[Dict[str, Any]]
    local_result: LocalResult
    kqml_turns: int = 0
    tokens_agent2: int = 0
    kqml_exchanges: List[Dict[str, Any]] = field(default_factory=list)
    phase1_ms: float = 0.0   # SQL write + local lookup + gap detection
    phase2_ms: float = 0.0   # KQML round trip to Agent-2 (0 if no gaps)
    phase3_ms: float = 0.0   # merge


@dataclass
class Shape:
    """One place's shape, and which agent it came from."""
    entity_name: str          # the name as stored
    entity_type: str
    wkt: str
    srid: int
    source: str = "Agent-1"


@dataclass
class Exchange:
    """Everything that crossed the wire for one question: one turn per
    request/reply pair (Section 1.8)."""
    kqml_turns: int = 0
    tokens_agent2: int = 0
    messages: List[Dict[str, Any]] = field(default_factory=list)
    local_ms: float = 0.0     # time spent writing + running our own SQL for shapes
    peer_ms: float = 0.0      # time spent waiting for Agent-2

    def record(self, resp: Dict[str, Any]) -> None:
        self.kqml_turns += 1
        self.tokens_agent2 += resp.get("tokens_agent2", 0) or 0
        if "ask_message" in resp and "tell_message" in resp:
            self.messages.append({"ask": resp["ask_message"], "tell": resp["tell_message"]})


def ask_agent2(what: str, call: Callable[..., Dict[str, Any]], *args, exchange: Exchange) -> Dict[str, Any]:
    """Send one ask to Agent-2, retrying up to 3 times. Returns the reply, or
    an empty one if Agent-2 could not be reached (the gap then stays open)."""
    started = time.perf_counter()
    for attempt in range(1, 4):
        try:
            resp = call(*args)
            exchange.peer_ms += (time.perf_counter() - started) * 1000
            exchange.record(resp)
            log.info("       | Agent-2 replied to %s ask (attempt %d): %d found",
                     what, attempt, len(resp.get("found", [])))
            return resp
        except Exception as exc:                    # noqa: BLE001 — peer down must not fail the query
            log.warning("       | Agent-2 %s ask, attempt %d failed - %s", what, attempt, exc)
            if attempt < 3:
                time.sleep(1.0 * attempt)
    exchange.peer_ms += (time.perf_counter() - started) * 1000
    log.warning("       | Agent-2 unreachable after 3 attempts - %s gap stays open", what)
    return {}


def _peer():
    from ..messaging.peer_client import PeerClient   # deferred: peer_client imports GapSlot from here
    return PeerClient()


# ═══════════════════════════════════════════════════════════════════════════
# VALUES — Scenarios 1-8
# ═══════════════════════════════════════════════════════════════════════════

def fetch_values(question: str, names: List[str], years: List[int], attributes: List[str],
                 entity_type: str, queries: List[str]) -> Dict[Tuple[str, int], Dict[str, Any]]:
    """Steps 1-2: SqlWriter writes the fetch, it runs, and every returned row
    comes back as {(place, year): {attribute: value}}."""
    rows = write_and_run(
        question, "DIRECT_LOOKUP", "fetch",
        shown={"entity_type": entity_type, "spatial": names, "temporal": years, "attributes": attributes},
        bind={"names": names, "years": years},
        required=["entity_name", "year", *attributes], queries=queries, label="value fetch (local)",
    )
    return {(r["entity_name"], r["year"]): {a: r[a] for a in attributes} for r in rows}


def held_anywhere(names: List[str], entity_type: str, queries: List[str]) -> set:
    """Which of `names` have any row here, in any year — the test that tells
    a spatial gap from a temporal one (Section 1.5)."""
    rows = write_and_run(
        f"Which of these {entity_type} names have any row at all: {names}", "DIRECT_LOOKUP", "presence",
        shown={"entity_type": entity_type, "spatial": names},
        bind={"names": names},
        required=["entity_name"], queries=queries, label="presence check (local)",
    )
    return {r["entity_name"] for r in rows}


def detect_gaps(names: List[str], years: List[int], attributes: List[str],
                by_slot: Dict[Tuple[str, int], Dict[str, Any]], entity_type: str,
                held: Optional[set] = None) -> Tuple[List[DataRecord], List[GapSlot], Dict[str, Any]]:
    """Step 3: split the request into found values and gap blocks.

    A slot is missing when its row is absent or its value is NULL. Places
    that miss exactly the same years and attributes share one GapSlot, so
    Agent-2 gets as few blocks as possible (Scenarios 5 and 6). `held` is the
    set of places with any row at all; with it each missing slot is also
    classified spatial / temporal / thematic for the gap signature."""
    found: List[DataRecord] = []
    per_place: Dict[Tuple[str, Tuple[str, ...]], List[int]] = {}
    miss_spatial, miss_temporal, miss_attr = [], [], []

    for name in names:
        for year in years:
            row = by_slot.get((name, year))
            values = row or {}
            present = {a: v for a, v in values.items() if v is not None}
            missing = tuple(a for a in attributes if a not in present)
            if present:
                found.append(DataRecord(state=name, year=year, values=present))
                log.info("       | FOUND : %s %d -> %s", name, year, present)
            if not missing:
                continue
            per_place.setdefault((name, missing), []).append(year)
            if row is not None:
                kind = "thematic"
                miss_attr.append(f"{name} {year} {list(missing)}")
            elif held is not None and name not in held:
                kind = "spatial"
                miss_spatial.append(f"{name} {year}")
            else:
                kind = "temporal"
                miss_temporal.append(f"{name} {year}")
            log.info("       | GAP   : %s %d -> %s (%s)", name, year, list(missing), kind)

    blocks: Dict[Tuple[Tuple[int, ...], Tuple[str, ...]], List[str]] = {}
    for (name, missing), yrs in per_place.items():
        blocks.setdefault((tuple(yrs), missing), []).append(name)
    gaps = [GapSlot(spatial=places, temporal=list(yrs), attributes=list(attrs), entity_type=entity_type)
            for (yrs, attrs), places in blocks.items()]

    signature = gap_signature(bool(miss_spatial), bool(miss_temporal), bool(miss_attr))
    diagnosis = {"a1_has": [f"{r.state} {r.year}" for r in found],
                 "missing_spatial": miss_spatial, "missing_temporal": miss_temporal,
                 "missing_attribute": miss_attr, "gap_signature": list(signature)}
    log.info("       | %d value(s) found, %d gap block(s), gap signature %s", len(found), len(gaps), signature)
    return found, gaps, diagnosis


def answer_query(params: QueryParams) -> AnsweredQuery:
    """The whole data path: write SQL → run → find gaps → ask Agent-2 → merge."""
    from ..result.merger import merge_results   # deferred: merger imports DataRecord from here

    entity_type = params.entity_type or DEFAULT_ENTITY_TYPE
    names = list(GERMAN_STATES) if "all" in params.spatial else list(params.spatial)
    queries: List[str] = []
    exchange = Exchange()

    t0 = time.perf_counter()
    by_slot = fetch_values(params.raw_query, names, params.temporal, params.attributes, entity_type, queries)
    no_rows = [n for n in names if not any((n, y) in by_slot for y in params.temporal)]
    held = (held_anywhere(no_rows, entity_type, queries) | (set(names) - set(no_rows))
            if no_rows else set(names))
    found, gaps, diagnosis = detect_gaps(names, params.temporal, params.attributes, by_slot, entity_type, held)
    t1 = time.perf_counter()

    resp: Dict[str, Any] = {}
    if gaps:
        resp = ask_agent2("data", _peer().ask_data, gaps, exchange=exchange)
    else:
        log.info("       | No gaps - Agent-2 not needed")
    t2 = time.perf_counter()

    merged = merge_results(found, resp.get("found", []),
                           requested_states=params.spatial, requested_years=params.temporal,
                           requested_attrs=params.attributes)
    t3 = time.perf_counter()

    return AnsweredQuery(
        merged=merged,
        local_result=LocalResult(found=found, gaps=gaps, queries=queries, diagnosis=diagnosis),
        kqml_turns=exchange.kqml_turns, tokens_agent2=exchange.tokens_agent2,
        kqml_exchanges=exchange.messages,
        phase1_ms=(t1 - t0) * 1000, phase2_ms=(t2 - t1) * 1000, phase3_ms=(t3 - t2) * 1000,
    )


# ═══════════════════════════════════════════════════════════════════════════
# SHAPES — Scenarios 9-12, and the inputs of 13-20
# ═══════════════════════════════════════════════════════════════════════════

def fetch_shapes(entities: List[Tuple[str, str]], queries: List[str]
                 ) -> Tuple[Dict[Tuple[str, str], Shape], Dict[Tuple[str, str], str]]:
    """Steps 1-3 for shapes. `entities` are (name, entity_type) pairs.
    Returns (found, missing): found maps each requested pair to its Shape;
    missing maps each requested pair that has no shape here to its miss mode,
    "unknown-feature" (no row) or "geometry-null" (row exists, shape NULL).
    One SqlWriter statement per entity type. The model is told only which
    shapes to fetch, never the user's question: a question such as "do X and
    Y touch?" would otherwise tempt it to compute the answer in the fetch."""
    found: Dict[Tuple[str, str], Shape] = {}
    missing: Dict[Tuple[str, str], str] = {}

    by_type: Dict[str, List[Tuple[str, str]]] = {}
    for name, entity_type in entities:
        by_type.setdefault(entity_type, []).append((name, entity_type))

    for entity_type, pairs in by_type.items():
        stored = {pair: normalize_entity_name(pair[0], entity_type) for pair in pairs}
        names = sorted(set(stored.values()))
        fetched = write_and_run(
            f"Fetch the stored shapes of these {entity_type} names: {names}", "GEOMETRY_LOOKUP", "fetch",
            shown={"entity_type": entity_type, "spatial": names},
            bind={"names": names},
            required=["entity_name", "wkt", "srid"], queries=queries, label=f"{entity_type} shape fetch (local)",
        )
        rows = {r["entity_name"]: r for r in fetched}
        for pair, name in stored.items():
            row = rows.get(name)
            if row is not None and row["wkt"]:
                found[pair] = Shape(row["entity_name"], entity_type, row["wkt"], row["srid"] or 4326)
                log.info("       | SHAPE : %s (%s) found", name, entity_type)
            else:
                missing[pair] = "geometry-null" if row is not None else "unknown-feature"
                log.info("       | GAP   : %s (%s) -> %s", name, entity_type, missing[pair])
    return found, missing


def get_shapes(entities: List[Tuple[str, str]], queries: List[str], exchange: Exchange) -> Tuple[Dict[Tuple[str, str], Shape], Dict[Tuple[str, str], str]]:
    """Steps 1-5 for shapes: fetch locally, ask Agent-2 for the gap in one
    :missing-geometries message, merge. The request names each place and its
    entity type only; why it is missing and what it is wanted for stay here
    (Scenarios 9, 13). Returns (shapes, still_missing) keyed by the requested
    (name, entity_type) pairs; still_missing carries the local miss mode."""
    started = time.perf_counter()
    shapes, missing = fetch_shapes(entities, queries)
    exchange.local_ms += (time.perf_counter() - started) * 1000
    if not missing:
        return shapes, {}

    slots, slot_pair = [], {}
    for pair in missing:
        name, entity_type = pair
        stored = normalize_entity_name(name, entity_type)
        try:
            slots.append(MessageFactory.missing_geometry_slot(spatial_entity=stored, entity_type=entity_type))
            slot_pair[(stored.lower(), entity_type)] = pair
        except Exception as exc:                    # noqa: BLE001 — a type the protocol cannot carry
            log.warning("       | Cannot ask Agent-2 for %r (%s): %s", name, entity_type, exc)

    if slots:
        resp = ask_agent2("geometry", _peer().ask_geometry, slots, exchange=exchange)
        for fg in resp.get("found", []):
            pair = slot_pair.get((fg.spatial_entity.lower(), fg.entity_type))
            if pair is not None:
                shapes[pair] = Shape(fg.spatial_entity, fg.entity_type, fg.geometry, fg.srid, source="Agent-2")
    still_missing = {pair: mode for pair, mode in missing.items() if pair not in shapes}
    if still_missing:
        log.info("       | Shapes held by neither agent: %s", sorted(still_missing))
    return shapes, still_missing


# ═══════════════════════════════════════════════════════════════════════════
# Agent-2 asks us — the same fetches, answering instead of asking
# ═══════════════════════════════════════════════════════════════════════════

def lookup_for_peer(slot) -> Dict[str, Any]:
    """Answer one of Agent-2's :missing-slots entries from our own data.
    Reports, per place, only the years still missing here."""
    names = slot.spatial if isinstance(slot.spatial, list) else [slot.spatial]
    years, attributes = list(slot.temporal), list(slot.attributes)
    entity_type = getattr(slot, "entity_type", None) or DEFAULT_ENTITY_TYPE
    queries: List[str] = []

    question = f"Agent-2 asks for {', '.join(attributes)} of {', '.join(names)} in {years}"
    by_slot = fetch_values(question, names, years, attributes, entity_type, queries)
    found, _gaps, _diagnosis = detect_gaps(names, years, attributes, by_slot, entity_type)

    satisfied = {(r.state, r.year) for r in found}
    missing_by_state = {n: [y for y in years if (n, y) not in satisfied] for n in names}
    missing_by_state = {n: ys for n, ys in missing_by_state.items() if ys}

    return {"found": [{"spatial": r.state, "year": r.year, **r.values} for r in found],
            "missing": list(missing_by_state),
            "missing_by_state": missing_by_state,
            "queries": queries}


def shapes_for_peer(slots) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Answer Agent-2's :missing-geometries entries from our own shapes.
    Returns (found_geometries, missing_geometries) in wire form."""
    pairs = [(s.spatial_entity, s.entity_type) for s in slots]
    shapes, missing = fetch_shapes(pairs, [])
    found = [{"spatial_entity": s.entity_name, "entity_type": s.entity_type,
              "geometry": s.wkt, "srid": s.srid} for s in shapes.values()]
    still = [{"spatial_entity": name, "entity_type": entity_type} for (name, entity_type) in missing]
    return found, still
