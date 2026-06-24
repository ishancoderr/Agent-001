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

    # Count total missing data points being asked
    total_missing_pts = sum(
        len(gap.temporal) * len(gap.attributes) for gap in gaps
    )
    log.info("       │ Sending KQML ask to Agent-2")
    log.info("       │ Required slots : %d", total_missing_pts)
    log.info("       │ Posting to %s ...", AGENT2_URL)

    response = httpx.post(
        f"{AGENT2_URL}/kqml/receive",
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()

    tell = JSONSerializer.from_dict(response.json())

    found: List[Dict] = []
    still_missing: List[str] = []

    for slot in tell.content.found_slots:
        for record in slot.data:
            flat = record.to_flat_dict()
            found.append(flat)

    for slot in tell.content.missing_slots:
        s = slot.spatial
        states = [s] if isinstance(s, str) else list(s)
        still_missing.extend(states)

    found_pts = sum(
        len(v) for v in [
            {k: v for k, v in r.items() if k not in ("spatial", "year")}
            for r in found
        ]
    )

    tokens_agent2 = 0
    if hasattr(tell, "metadata") and tell.metadata is not None:
        tokens_agent2 = getattr(tell.metadata, "token_usage", 0) or 0

    log.info("       │ Agent-2 filled : %d data points", found_pts)
    log.info("       │ Agent-2 tokens : %d", tokens_agent2)
    if still_missing:
        log.info("       │ Still missing  : %s", sorted(set(still_missing)))

    return {"found": found, "missing": still_missing, "tokens_agent2": tokens_agent2}
