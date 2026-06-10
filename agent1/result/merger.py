from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..retrieval.gap_detector import DataRecord

log = logging.getLogger("agent1.result.merger")


def merge_results(
    local: List[DataRecord],
    agent2_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []

    for r in local:
        entry = {"state": r.state, "year": r.year, "source": "Agent-1", **r.values}
        merged.append(entry)
        log.info("       │ [Agent-1] %s %d → %s", r.state, r.year, r.values)

    for rec in agent2_data:
        entry: Dict[str, Any] = {"source": "Agent-2"}
        entry["state"] = rec.pop("spatial", rec.get("state", ""))
        entry["year"]  = rec.get("year", "")
        entry.update({k: v for k, v in rec.items() if k not in ("state", "year")})
        merged.append(entry)
        log.info("       │ [Agent-2] %s %s → %s",
                 entry["state"], entry["year"],
                 {k: v for k, v in entry.items() if k not in ("state", "year", "source")})

    merged.sort(key=lambda x: (x.get("state", ""), x.get("year", 0)))
    log.info("       │ Sorted merged list: %d records", len(merged))
    return merged
