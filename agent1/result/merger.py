from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..messaging.agent_registry import AGENT_NAME, PRIMARY_PEER
from ..pipeline.gazetteer import names_of
from ..retrieval.gap_detector import DataRecord

log = logging.getLogger("agent1.result.merger")


def merge_results(
    local: List[DataRecord],
    peer_data: List[Dict[str, Any]],
    requested_places: Optional[List[str]] = None,
    requested_years: Optional[List[int]] = None,
    requested_attrs: Optional[List[str]] = None,
    entity_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Our records plus the peer's, one row per (place, year), each tagged
    with the agent it came from (names from .env). Rows are keyed by `spatial` — the place's name, the same field
    name the KQML wire uses — for whatever entity type the question is about;
    "all" expands to every member of `entity_type`."""
    # Build lookup keyed by (place, year) so the peer fills into existing rows
    merged: Dict[tuple, Dict[str, Any]] = {}

    for r in local:
        key = (r.spatial, r.year)
        entry = {"spatial": r.spatial, "year": r.year, "source": AGENT_NAME, **r.values}
        merged[key] = entry
        log.info("       │ [%s] %s %d → %s", AGENT_NAME, r.spatial, r.year, r.values)

    for rec in peer_data:
        place = rec.pop("spatial", "")
        year  = rec.get("year", "")
        key   = (place, year)
        attrs = {k: v for k, v in rec.items() if k != "year"}

        if key in merged:
            # Fill missing attributes into our existing row
            merged[key].update(attrs)
            merged[key]["source"] = f"{AGENT_NAME}+{PRIMARY_PEER}"
            log.info("       │ [%s fill] %s %s → added %s", PRIMARY_PEER, place, year, attrs)
        else:
            entry = {"spatial": place, "year": year, "source": PRIMARY_PEER, **attrs}
            merged[key] = entry
            log.info("       │ [%s new ] %s %s → %s", PRIMARY_PEER, place, year, attrs)

    if requested_places and requested_years and requested_attrs:
        places = names_of(entity_type) if "all" in requested_places else requested_places

        # Fill completely absent (place, year) pairs with all-null placeholder
        for place in places:
            for year in requested_years:
                key = (place, year)
                if key not in merged:
                    entry: Dict[str, Any] = {
                        "spatial": place,
                        "year":    year,
                        "source":  "missing",
                    }
                    for attr in requested_attrs:
                        entry[attr] = None
                    merged[key] = entry
                    log.info("       │ [MISSING     ] %s %d → all null", place, year)

        # Ensure every merged row has ALL requested attrs (null if absent)
        for key, entry in merged.items():
            for attr in requested_attrs:
                if attr not in entry:
                    entry[attr] = None
                    log.info("       │ [FILL NULL   ] %s %s → %s=null",
                             entry.get("spatial"), entry.get("year"), attr)

    result = sorted(merged.values(), key=lambda x: (x.get("spatial", ""), x.get("year", 0)))
    log.info("       │ Sorted merged list: %d records", len(result))
    return result
