"""
Build a KQML 'ask' message from gap slots, POST it to Agent 2,
and parse the 'tell' response back into found/missing lists.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from kqml_messaging import MessageFactory, MissingSlot
from kqml_messaging.serializers import JSONSerializer

from .agent_registry import AGENT_REGISTRY
from ..retrieval.gap_detector import GapSlot

log = logging.getLogger("agent1.messaging.kqml_client")

AGENT2_URL = AGENT_REGISTRY.get("Agent-2", "http://localhost:8001")


def send_kqml_ask(gaps: List[GapSlot]) -> Dict[str, Any]:
    missing_slots: List[MissingSlot] = [
        MessageFactory.missing_slot(
            spatial=gap.spatial[0] if len(gap.spatial) == 1 else gap.spatial,
            temporal=gap.temporal,
            attributes=gap.attributes,
        )
        for gap in gaps
    ]

    msg = MessageFactory.ask(
        sender="Agent-1",
        receiver="Agent-2",
        missing_slots=missing_slots,
    )

    payload = JSONSerializer.to_dict(msg)

    log.info("       │ KQML ask built")
    log.info("       │ reply_with  : %s", msg.reply_with)
    log.info("       │ Slots       : %d", len(missing_slots))
    for i, slot in enumerate(missing_slots, 1):
        log.info("       │   Slot %d: spatial=%s  temporal=%s  attrs=%s",
                 i, slot.spatial, slot.temporal, slot.attributes)
    log.info("       │ Posting to %s/kqml/receive ...", AGENT2_URL)

    response = httpx.post(
        f"{AGENT2_URL}/kqml/receive",
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()

    log.info("       │ Response status : HTTP %d", response.status_code)

    tell = JSONSerializer.from_dict(response.json())

    log.info("       │ KQML tell received")
    log.info("       │ in_reply_to  : %s", tell.in_reply_to)
    log.info("       │ found_slots  : %d", len(tell.content.found_slots))
    log.info("       │ missing_slots: %d", len(tell.content.missing_slots))

    found: List[Dict] = []
    still_missing: List[str] = []

    for slot in tell.content.found_slots:
        log.info("       │ Found slot: spatial=%s  records=%d", slot.spatial, len(slot.data))
        for record in slot.data:
            flat = record.to_flat_dict()
            log.info("       │   Record: %s", flat)
            found.append(flat)

    for slot in tell.content.missing_slots:
        s = slot.spatial
        states = [s] if isinstance(s, str) else list(s)
        log.info("       │ Still missing: %s", states)
        still_missing.extend(states)

    return {"found": found, "missing": still_missing}
