"""
Ask Agent-2 for the WKT geometry of one or more named features.
Used for geometry-exchange scenarios (9-13), and for Scenario 21's buffer-and-test
exchange where the targets that satisfy the query cannot be named in advance.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from kqml_messaging import EntityType, MissingGeometrySlot, FoundGeometrySlot, MessageFactory
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
    tell_payload = response.json()

    tell = JSONSerializer.from_dict(tell_payload)

    found:   List[FoundGeometrySlot]   = list(tell.content.found_geometries  or [])
    missing: List[MissingGeometrySlot] = list(tell.content.missing_geometries or [])

    for fg in found:
        log.info("       │ Geometry received : %s (%s) srid=%s  wkt=%.60s…",
                 fg.spatial_entity, fg.entity_type.value, fg.srid, fg.geometry)
    if missing:
        log.info("       │ Still missing geometries: %s",
                 [(m.spatial_entity, m.entity_type.value) for m in missing])

    return {"found": found, "missing": missing, "ask_message": payload, "tell_message": tell_payload}


def send_kqml_city_buffer_ask(wkt: str, srid: int, exclude: List[str]) -> Dict[str, Any]:
    """
    Scenario 21: ask Agent-2 to test its own city catalogue against a
    constructed buffer zone, since the cities that satisfy the query cannot
    be named in advance. Returns {"found": List[FoundGeometrySlot]}.
    """
    sq = MessageFactory.spatial_query(
        topic="Within", geometry=wkt, target_entity=EntityType.CITY, srid=srid, exclude=exclude,
    )
    msg = MessageFactory.ask_spatial_query(sender="Agent-1", receiver="Agent-2", spatial_query=sq)
    payload = JSONSerializer.to_dict(msg)

    log.info("       │ Sending KQML city-buffer ask to Agent-2 (exclude=%d)", len(exclude))
    log.info("       │ Posting to %s ...", AGENT2_URL)

    response = httpx.post(
        f"{AGENT2_URL}/kqml/receive",
        json=payload,
        timeout=httpx.Timeout(connect=3.0, read=15.0, write=5.0, pool=3.0),
    )
    response.raise_for_status()
    tell_payload = response.json()

    tell = JSONSerializer.from_dict(tell_payload)
    found: List[FoundGeometrySlot] = list(tell.content.found_geometries or [])

    for fg in found:
        log.info("       │ City received : %s srid=%s  %.40s…", fg.spatial_entity, fg.srid, fg.geometry)

    return {"found": found, "ask_message": payload, "tell_message": tell_payload}
