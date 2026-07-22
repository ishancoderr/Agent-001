"""
POST /kqml/receive  — handles incoming KQML 'ask' messages from peer agents
                      (supports bidirectional Agent-2 → Agent-1 queries,
                       including geometry-exchange scenarios 11-13)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from kqml_messaging import MissingSlot, MissingGeometrySlot

from ..retrieval import execute_local_lookup_from_slots
from ..retrieval.geometry_resolver import resolve_geometries

log = logging.getLogger("agent1.controller.kqml")
router = APIRouter()

SEPARATOR = "_" * 60


class KQMLMessage(BaseModel):
    sender:      str
    receiver:    str
    reply_with:  Optional[str] = None
    in_reply_to: Optional[str] = None
    language:    str = "GeoSQL"
    ontology:    str = "German-Geostats-v1"
    content:     Dict[str, Any]


@router.post("/kqml/receive")
def receive_kqml(msg: KQMLMessage):
    log.info(SEPARATOR)
    log.info("                       START")
    log.info("       Incoming KQML request received by Agent 1")
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

        result = execute_local_lookup_from_slots(slot)
        log.info("       │   → found=%d  missing=%s",
                 len(result["found"]), result["missing"] or "none")

        if result["found"]:
            found_slots.append({
                "spatial":    slot.spatial,
                "temporal":   slot.temporal,
                "attributes": slot.attributes,
                "data":       result["found"],
            })
        if result["missing"]:
            missing_slots.append({
                "spatial":    result["missing"],
                "temporal":   slot.temporal,
                "attributes": slot.attributes,
            })

    # ── Geometry slots (scenarios 11-13) ──────────────────────────────────────
    found_geometries:   List[Dict] = []
    missing_geometries: List[Dict] = []

    if raw_geometry_slots:
        geo_slot_objs = [MissingGeometrySlot(**g) for g in raw_geometry_slots]
        resolved, unresolved = resolve_geometries(geo_slot_objs)

        for fg in resolved:
            found_geometries.append({
                "spatial_entity": fg.spatial_entity,
                "entity_type":    fg.entity_type,
                "geometry":       fg.geometry,
                "srid":           fg.srid,
            })
        for mg in unresolved:
            missing_geometries.append({
                "spatial_entity": mg.spatial_entity,
                "entity_type":    mg.entity_type,
            })

    log.info("KQML   │ Reply: found_slots=%d  missing_slots=%d  "
             "found_geometries=%d  missing_geometries=%d",
             len(found_slots), len(missing_slots),
             len(found_geometries), len(missing_geometries))
    log.info(SEPARATOR)

    return {
        "performative": "tell",
        "sender":       "Agent-1",
        "receiver":     msg.sender,
        "in_reply_to":  msg.reply_with,
        "language":     "GeoSQL",
        "ontology":     "German-Geostats-v1",
        "metadata":     {"token_usage": 0},
        "content": {
            "found_slots":        found_slots,
            "missing_slots":      missing_slots,
            "found_geometries":   found_geometries,
            "missing_geometries": missing_geometries,
        },
    }
