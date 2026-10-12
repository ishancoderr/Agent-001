"""
POST /kqml/receive  — handles incoming KQML 'ask' messages from peer agents
                      (supports bidirectional Agent-2 → Agent-1 queries,
                       including geometry-exchange scenarios 9-12 and the
                       delegated zone test of scenario 20)

Every answer comes from the same SqlWriter fetches the /query path uses —
this side only answers; it never asks a third agent.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from kqml_messaging import Encoding, Language, MissingSlot, MissingGeometrySlot, Ontology

from ..messaging.agent_registry import AGENT_NAME
from ..pipeline.query_params import DEFAULT_ZONE_TARGET, ENTITY_SRID, ZONE_SEARCH_TYPES
from ..retrieval.gap_detector import lookup_for_peer, shapes_for_peer
from ..retrieval.spatial_compute import zone_for_peer

log = logging.getLogger("agent1.controller.kqml")
router = APIRouter()

SEPARATOR = "_" * 60


class KQMLMessage(BaseModel):
    sender:      str
    receiver:    str
    reply_with:  Optional[str] = None
    in_reply_to: Optional[str] = None
    language:    str = Language.GEOKQML.value          # vocabulary from the shared kqml_messaging package
    encoding:    str = Encoding.JSON.value
    ontology:    str = Ontology.GEO_MISSINGNESS_V2.value
    content:     Dict[str, Any]


@router.post("/kqml/receive")
def receive_kqml(msg: KQMLMessage):
    log.info(SEPARATOR)
    log.info("                       START")
    log.info("       Incoming KQML request received by %s", AGENT_NAME)
    log.info(SEPARATOR)
    log.info("KQML   │ From: %s  req=%s", msg.sender, msg.reply_with)

    raw_data_slots     = msg.content.get("missing_slots", [])
    raw_geometry_slots = msg.content.get("missing_geometries", [])

    log.info("       │ Data slots: %d  Geometry slots: %d",
             len(raw_data_slots), len(raw_geometry_slots))

    # ── Data slots ────────────────────────────────────────────────────────────
    found_slots:   List[Dict] = []
    missing_slots: List[Dict] = []

    for i, slot_raw in enumerate(raw_data_slots, 1):
        slot = MissingSlot(**slot_raw)
        log.info("       │ Data slot %d: spatial=%s  temporal=%s  attrs=%s",
                 i, slot.spatial, slot.temporal, slot.attributes)

        result = lookup_for_peer(slot, msg.sender)
        log.info("       │   → found=%d  missing=%s",
                 len(result["found"]), result["missing"] or "none")

        if result["found"]:
            found_slots.append({
                "spatial":     slot.spatial,
                "temporal":    slot.temporal,
                "attributes":  slot.attributes,
                "data":        result["found"],
                "entity_type": slot.entity_type,
            })
        # Group states by their actual residue years (not the original requested
        # range) so the peer only re-asks a third agent for what is genuinely
        # still missing, rather than re-requesting data just handed to it above.
        by_years: Dict[tuple, List[str]] = {}
        for state, years in result.get("missing_by_state", {}).items():
            by_years.setdefault(tuple(years), []).append(state)
        for years, states in by_years.items():
            missing_slots.append({
                "spatial":     states if len(states) > 1 else states[0],
                "temporal":    list(years),
                "attributes":  slot.attributes,
                "entity_type": slot.entity_type,
            })

    # ── Geometry slots (scenarios 9-12) ───────────────────────────────────────
    found_geometries:   List[Dict] = []
    missing_geometries: List[Dict] = []

    if raw_geometry_slots:
        geo_slot_objs = [MissingGeometrySlot(**g) for g in raw_geometry_slots]
        found_geometries, missing_geometries = shapes_for_peer(geo_slot_objs)

    # ── Spatial query (Scenario 20: delegated zone test) ──────────────────────
    # The peer sends a constructed shape because the targets that satisfy it
    # cannot be named in advance; test it against our OWN catalogue rather than
    # looking anything up by name.
    raw_spatial_query = msg.content.get("spatial_query")
    if raw_spatial_query:
        wkt      = raw_spatial_query.get("geometry", "")
        exclude  = raw_spatial_query.get("exclude", [])
        target   = raw_spatial_query.get("target_entity") or DEFAULT_ZONE_TARGET
        srid     = raw_spatial_query.get("srid") or ENTITY_SRID.get(target)
        log.info("       │ Spatial query: topic=%s target=%s exclude=%d",
                 raw_spatial_query.get("topic"), target, len(exclude))
        if target in ZONE_SEARCH_TYPES:            # entities.yaml: zone_search: true
            matches = zone_for_peer(wkt, srid, exclude, target, msg.sender)
            found_geometries.extend(matches)
            log.info("       │ Spatial query matches in our catalogue: %d", len(matches))
        else:
            log.warning("       │ Spatial query target %r is not zone-searchable here — nothing tested", target)

    log.info("KQML   │ Reply: found_slots=%d  missing_slots=%d  "
             "found_geometries=%d  missing_geometries=%d",
             len(found_slots), len(missing_slots),
             len(found_geometries), len(missing_geometries))
    log.info(SEPARATOR)

    return {
        "performative": "tell",
        "sender":       AGENT_NAME,
        "receiver":     msg.sender,
        "in_reply_to":  msg.reply_with,
        "language":     Language.GEOKQML.value,
        "encoding":     Encoding.JSON.value,
        "ontology":     Ontology.GEO_MISSINGNESS_V2.value,
        "metadata":     {"token_usage": 0},
        "content": {
            "found_slots":        found_slots,
            "missing_slots":      missing_slots,
            "found_geometries":   found_geometries,
            "missing_geometries": missing_geometries,
        },
    }
