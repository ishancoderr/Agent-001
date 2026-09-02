"""
Resolve MissingGeometrySlot requests against Agent-1's local cities/states catalog.
Returns WKT geometries (SRID 4326) for cities (centroid) and states (geo_shape).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text

from kqml_messaging import EntityType, MissingGeometrySlot, FoundGeometrySlot, MessageFactory, check_srid_agreement

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
    queries: Optional[List[str]] = None,
) -> Tuple[List[FoundGeometrySlot], List[MissingGeometrySlot]]:
    """
    Try to resolve each slot from the local DB.
    Returns (found_list, still_missing_list). When `queries` is given, every
    SQL statement actually run against Agent-1's DB is appended to it, for
    evaluation-log tracing.
    """
    found:   List[FoundGeometrySlot]   = []
    missing: List[MissingGeometrySlot] = []

    db = SessionLocal()
    try:
        for slot in slots:
            entity_type = slot.entity_type.value  # plain str, not the EntityType repr, for logging
            wkt, matched_name = _lookup(slot.spatial_entity, entity_type, db, queries=queries)
            if wkt is not None:
                log.info("       │ Geometry FOUND : %s → %s (%s)",
                         slot.spatial_entity, matched_name, entity_type)
                found.append(
                    MessageFactory.found_geometry_slot(
                        spatial_entity=matched_name,   # actual DB name
                        entity_type=slot.entity_type,
                        geometry=wkt,
                        srid=4326,
                    )
                )
            else:
                log.info("       │ Geometry MISSING: %s (%s)", slot.spatial_entity, entity_type)
                missing.append(slot)
    finally:
        db.close()

    return found, missing


def _lookup(entity_name: str, entity_type: str, db, queries: Optional[List[str]] = None) -> str | None:
    """
    Try to find the entity in the DB using multiple name forms:
    1. Exact match
    2. Alias (German↔English)
    3. Case-insensitive ILIKE
    4. Partial ILIKE (shortest match wins)
    Returns WKT string or None. When `queries` is given, every attempted SQL
    statement (values substituted, for readability) is appended to it.
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
        sql = (f"SELECT ST_AsText({col}), {name_col} FROM {table} "
               f"WHERE {name_col} = '{name}' AND ST_AsText({col}) IS NOT NULL LIMIT 1")
        if queries is not None:
            queries.append(sql)
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
        sql = f"SELECT 1 FROM {table} WHERE {name_col} = '{name}' LIMIT 1"
        if queries is not None:
            queries.append(sql)
        exists = db.execute(
            text(f"SELECT 1 FROM {table} WHERE {name_col} = :n LIMIT 1"),
            {"n": name},
        ).fetchone()
        if exists:
            log.info("       │ %s %r found in DB but geometry is NULL — will ask peer", entity_type, name)
            return None, None

    # 3 — entity not in DB at all: try case-insensitive full match with valid geometry
    for name in candidates:
        sql = (f"SELECT ST_AsText({col}), {name_col} FROM {table} "
               f"WHERE {name_col} ILIKE '{name}' AND ST_AsText({col}) IS NOT NULL LIMIT 1")
        if queries is not None:
            queries.append(sql)
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


# ── Buffer / within (Scenario 21: target that cannot be named) ──────────────
# A city-distance query ("which cities lie within 100 km of X") cannot be
# expressed as a named missing-slot, since the cities that satisfy it are the
# answer, not the input. Instead a buffer zone is built once (locally, if the
# reference city is held; via the peer's geometry catalog otherwise) and sent
# to the peer as a shape to test its own catalog against, per Section 4's
# achieve/spatial-query pattern.

def build_city_buffer(
    ref_city: str, distance_km: float, queries: Optional[List[str]] = None,
) -> Optional[Dict[str, object]]:
    """Build a buffer polygon (metres) around a locally-held city's centroid.
    Returns {"ref_name", "wkt", "srid"} or None if the reference city isn't held here."""
    candidates = list(dict.fromkeys(filter(None, [
        _CITY_ALIASES.get(ref_city),
        _CITY_ALIASES.get(ref_city.title()),
        ref_city,
    ])))
    db = SessionLocal()
    try:
        for name in candidates:
            sql = (f"SELECT city_name, ST_AsText(ST_Buffer(centroid::geography, {distance_km * 1000})::geometry), "
                   f"ST_SRID(centroid) FROM cities WHERE city_name = '{name}' AND centroid IS NOT NULL LIMIT 1")
            if queries is not None:
                queries.append(sql)
            row = db.execute(
                text("""
                    SELECT city_name,
                           ST_AsText(ST_Buffer(centroid::geography, :dist)::geometry),
                           ST_SRID(centroid)
                    FROM cities
                    WHERE city_name = :n AND centroid IS NOT NULL
                    LIMIT 1
                """),
                {"n": name, "dist": distance_km * 1000},
            ).fetchone()
            if row:
                return {"ref_name": row[0], "wkt": row[1], "srid": row[2] or 4326}
        return None
    finally:
        db.close()


def buffer_from_point(
    wkt_point: str, srid: int, distance_km: float, queries: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Build a buffer polygon around an already-known point (e.g. one resolved
    from the peer), without requiring a local row for the reference city."""
    db = SessionLocal()
    try:
        sql = (f"SELECT ST_AsText(ST_Buffer(ST_GeomFromText('{wkt_point[:60]}...', {srid})"
               f"::geography, {distance_km * 1000})::geometry)")
        if queries is not None:
            queries.append(sql)
        row = db.execute(
            text("""
                SELECT ST_AsText(
                    ST_Buffer(ST_GeomFromText(:wkt, :srid)::geography, :dist)::geometry
                )
            """),
            {"wkt": wkt_point, "srid": srid, "dist": distance_km * 1000},
        ).fetchone()
        return {"wkt": row[0], "srid": srid}
    finally:
        db.close()


def cities_within_buffer(
    wkt: str, srid: int, exclude: Optional[List[str]] = None, queries: Optional[List[str]] = None,
) -> List[FoundGeometrySlot]:
    """Test the LOCAL cities catalog against a buffer polygon, per Scenario 21's
    achieve/spatial-query pattern: the peer runs the test over its own catalog
    rather than being asked for a fact it could have named."""
    exclude = [e for e in (exclude or []) if e]
    db = SessionLocal()
    try:
        sql = (f"SELECT city_name, ST_AsText(centroid), ST_SRID(centroid) FROM cities "
               f"WHERE centroid IS NOT NULL AND ST_Within(centroid, ST_GeomFromText('{wkt[:60]}...', {srid})) "
               f"AND NOT (city_name = ANY({exclude}))")
        if queries is not None:
            queries.append(sql)
        rows = db.execute(
            text("""
                SELECT city_name, ST_AsText(centroid), ST_SRID(centroid)
                FROM cities
                WHERE centroid IS NOT NULL
                  AND ST_Within(centroid, ST_GeomFromText(:wkt, :srid))
                  AND NOT (city_name = ANY(:exclude))
            """),
            {"wkt": wkt, "srid": srid, "exclude": exclude},
        ).fetchall()
        return [
            MessageFactory.found_geometry_slot(
                spatial_entity=r[0], entity_type=EntityType.CITY, geometry=r[1], srid=r[2] or srid,
            )
            for r in rows
        ]
    finally:
        db.close()


# ── Constructive operations (Section 3: Scenarios 13-16, 20) ────────────────
# Both agents run the same code, so an operation is never itself missing —
# only an input shape can be (Section 3.5). Every operation here first
# resolves each named entity's geometry (locally or via the existing
# missing-geometries exchange), then runs a local computation once all
# shapes have arrived. SRID agreement is checked before the operation is
# attempted, exactly as the document specifies, reusing the same check the
# kqml_messaging library exposes for this purpose.

_OP_SQL_FN = {
    "Union": "ST_Union",
    "Intersection": "ST_Intersection",
    "Difference": "ST_Difference",          # order matters: fn(A, B) = A minus B
    "SymDifference": "ST_SymDifference",
}


def resolve_named_geometry(
    name: str, entity_type: str, queries: Optional[List[str]] = None,
) -> Optional[Dict[str, object]]:
    """Look up a single named entity's geometry in the local catalogue.
    Tries the given entity_type first, then the other one — a BufferWithin
    reference is often a city while its targets are states (Scenario 20's own
    setup: "which of NRW and Niedersachsen lie within 100 km of Dortmund"), so
    a single declared entity_type for the whole operation isn't reliable per name.
    Returns {"name": matched_name, "wkt": ..., "srid": 4326} or None if not held here."""
    db = SessionLocal()
    try:
        for et in dict.fromkeys([entity_type, "city", "state"]):
            wkt, matched_name = _lookup(name, et, db, queries=queries)
            if wkt is not None:
                return {"name": matched_name, "wkt": wkt, "srid": 4326}
        return None
    finally:
        db.close()


def execute_operation(
    operation: str, geom_a: Dict[str, object], geom_b: Dict[str, object],
    queries: Optional[List[str]] = None,
) -> Dict[str, object]:
    """Run Union/Intersection/Difference/SymDifference on two already-resolved
    geometries. An operation on shapes held in different reference systems is an
    error, checked here before the operation runs rather than after it fails."""
    check_srid_agreement(geom_a["srid"], geom_b["srid"])
    fn = _OP_SQL_FN[operation]
    db = SessionLocal()
    try:
        sql = f"SELECT ST_AsText({fn}(<geom_a wkt>, <geom_b wkt>))"
        if queries is not None:
            queries.append(sql)
        row = db.execute(
            text(f"""
                SELECT ST_AsText({fn}(
                    ST_GeomFromText(:wkt_a, :srid_a),
                    ST_GeomFromText(:wkt_b, :srid_b)
                ))
            """),
            {"wkt_a": geom_a["wkt"], "srid_a": geom_a["srid"],
             "wkt_b": geom_b["wkt"], "srid_b": geom_b["srid"]},
        ).fetchone()
        return {"wkt": row[0], "srid": geom_a["srid"]}
    finally:
        db.close()


def fold_union(geometries: List[Dict[str, object]], queries: Optional[List[str]] = None) -> Dict[str, object]:
    """Union takes two shapes at a time; combining more than two is a fold across
    the pairwise operation, carrying the intermediate shape forward without a name
    (Section 3.3's explanation of how Union generalizes to a group)."""
    result = geometries[0]
    for g in geometries[1:]:
        result = execute_operation("Union", result, g, queries=queries)
    return result


def targets_within_buffer(
    ref_geom: Dict[str, object], distance_km: float, targets: List[Dict[str, object]],
    queries: Optional[List[str]] = None,
) -> List[Dict[str, object]]:
    """Named-target buffer test (Scenario 20): build a zone around ref_geom and test
    each already-resolved named target against it. Unlike Scenario 21's open-target
    buffer, this zone is purely local scratch and never crosses the wire, since every
    target is named and its shape was fetched the ordinary way."""
    db = SessionLocal()
    try:
        results = []
        for t in targets:
            sql = (f"SELECT ST_Intersects(<{t['name']} wkt>, "
                   f"ST_Buffer(<ref wkt>::geography, {distance_km * 1000})::geometry)")
            if queries is not None:
                queries.append(sql)
            row = db.execute(
                text("""
                    SELECT ST_Intersects(
                        ST_GeomFromText(:wkt_t, :srid_t),
                        ST_Buffer(ST_GeomFromText(:wkt_ref, :srid_ref)::geography, :dist)::geometry
                    )
                """),
                {"wkt_t": t["wkt"], "srid_t": t["srid"], "wkt_ref": ref_geom["wkt"],
                 "srid_ref": ref_geom["srid"], "dist": distance_km * 1000},
            ).fetchone()
            results.append({"name": t["name"], "meets_zone": bool(row[0])})
        return results
    finally:
        db.close()
