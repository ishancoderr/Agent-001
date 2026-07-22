"""
Resolve MissingGeometrySlot requests against Agent-1's local cities/states catalog.
Returns WKT geometries (SRID 4326) for cities (centroid) and states (geo_shape).
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from sqlalchemy import text

from kqml_messaging import MissingGeometrySlot, FoundGeometrySlot, MessageFactory

from ..database import SessionLocal

log = logging.getLogger("agent1.retrieval.geometry_resolver")

# German ↔ English city name aliases (same as spatial_validator)
_CITY_ALIASES: dict = {
    "München":    "Munich",
    "Munich":     "München",
    "Muenchen":   "München",
    "Köln":       "Cologne",
    "Cologne":    "Köln",
    "Koeln":      "Köln",
    "Nürnberg":   "Nuremberg",
    "Nuremberg":  "Nürnberg",
    "Nuernberg":  "Nürnberg",
    "Düsseldorf": "Dusseldorf",
    "Dusseldorf": "Düsseldorf",
    "Duesseldorf":"Düsseldorf",
}


def resolve_geometries(
    slots: List[MissingGeometrySlot],
) -> Tuple[List[FoundGeometrySlot], List[MissingGeometrySlot]]:
    """
    Try to resolve each slot from the local DB.
    Returns (found_list, still_missing_list).
    """
    found:   List[FoundGeometrySlot]   = []
    missing: List[MissingGeometrySlot] = []

    db = SessionLocal()
    try:
        for slot in slots:
            wkt, matched_name = _lookup(slot.spatial_entity, slot.entity_type, db)
            if wkt is not None:
                log.info("       │ Geometry FOUND : %s → %s (%s)",
                         slot.spatial_entity, matched_name, slot.entity_type)
                found.append(
                    MessageFactory.found_geometry_slot(
                        spatial_entity=matched_name,   # actual DB name
                        entity_type=slot.entity_type,
                        geometry=wkt,
                        srid=4326,
                    )
                )
            else:
                log.info("       │ Geometry MISSING: %s (%s)", slot.spatial_entity, slot.entity_type)
                missing.append(slot)
    finally:
        db.close()

    return found, missing


def _lookup(entity_name: str, entity_type: str, db) -> str | None:
    """
    Try to find the entity in the DB using multiple name forms:
    1. Exact match
    2. Alias (German↔English)
    3. Case-insensitive ILIKE
    4. Partial ILIKE (shortest match wins)
    Returns WKT string or None.
    """
    if entity_type not in ("city", "state"):
        log.warning("       │ Unknown entity_type %r for %r — skipping", entity_type, entity_name)
        return None

    # Build candidate name list — English alias first, then original German form
    candidates = list(dict.fromkeys(filter(None, [
        _CITY_ALIASES.get(entity_name),
        _CITY_ALIASES.get(entity_name.title()),
        entity_name,
    ])))

    table    = "cities" if entity_type == "city"  else "states"
    col      = "centroid" if entity_type == "city" else "geo_shape"
    name_col = "city_name" if entity_type == "city" else "state_name"

    # 1 — exact match with valid geometry (alias first, then original)
    for name in candidates:
        row = db.execute(
            text(f"""
                SELECT ST_AsText({col}), {name_col} FROM {table}
                WHERE {name_col} = :n AND ST_AsText({col}) IS NOT NULL
                LIMIT 1
            """),
            {"n": name},
        ).fetchone()
        if row:
            log.info("       │ Resolved (exact)  : %r → %r", entity_name, row[1])
            return row[0], row[1]

    # 2 — entity exists but geometry is NULL → stop here, do NOT fall through to partial
    for name in candidates:
        exists = db.execute(
            text(f"SELECT 1 FROM {table} WHERE {name_col} = :n LIMIT 1"),
            {"n": name},
        ).fetchone()
        if exists:
            log.info("       │ %s %r found in DB but geometry is NULL — will ask peer", entity_type, name)
            return None, None

    # 3 — entity not in DB at all: try case-insensitive full match with valid geometry
    for name in candidates:
        row = db.execute(
            text(f"""
                SELECT ST_AsText({col}), {name_col} FROM {table}
                WHERE {name_col} ILIKE :n AND ST_AsText({col}) IS NOT NULL
                LIMIT 1
            """),
            {"n": name},
        ).fetchone()
        if row:
            log.info("       │ Resolved (ilike)  : %r → %r", entity_name, row[1])
            return row[0], row[1]

    log.info("       │ %s %r not found in DB (tried: %s)", entity_type, entity_name, candidates)
    return None, None
