"""
Ask Agent-2 for the WKT geometry of one or more named features.
Used for geometry-exchange scenarios (11-13).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from kqml_messaging import MissingGeometrySlot, FoundGeometrySlot, MessageFactory
from kqml_messaging.serializers import JSONSerializer

from .agent_registry import AGENT_REGISTRY

log = logging.getLogger("agent1.messaging.kqml_geometry_client")

AGENT2_URL = AGENT_REGISTRY.get("Agent-2", "http://localhost:8001")


def send_kqml_geometry_ask(
    slots: List[MissingGeometrySlot],
) -> Dict[str, List]:
    """
    POST a KQML ask with geometry slots to Agent-2/kqml/receive.
    Returns {"found": List[FoundGeometrySlot], "missing": List[MissingGeometrySlot]}.
    """
    msg     = MessageFactory.ask(sender="Agent-1", receiver="Agent-2", missing_geometries=slots)
    payload = JSONSerializer.to_dict(msg)

    log.info("       │ Sending KQML geometry ask to Agent-2 (%d slots)", len(slots))
    log.info("       │ Posting to %s ...", AGENT2_URL)

    response = httpx.post(
        f"{AGENT2_URL}/kqml/receive",
        json=payload,
        timeout=httpx.Timeout(connect=3.0, read=15.0, write=5.0, pool=3.0),
    )
    response.raise_for_status()

    tell = JSONSerializer.from_dict(response.json())

    found:   List[FoundGeometrySlot]   = list(tell.content.found_geometries  or [])
    missing: List[MissingGeometrySlot] = list(tell.content.missing_geometries or [])

    for fg in found:
        log.info("       │ Geometry received : %s (%s) srid=%s  wkt=%.60s…",
                 fg.spatial_entity, fg.entity_type, fg.srid, fg.geometry)
    if missing:
        log.info("       │ Still missing geometries: %s",
                 [(m.entity_name, m.entity_type) for m in missing])

    return {"found": found, "missing": missing}
