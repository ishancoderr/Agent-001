"""
Reference ("gold") SQL for every SqlWriter step.

Built from config/schema/*.yaml in the same style as the worked examples in
config/prompts/sql/*.yaml, so a new attribute table or entity type gets its
gold SQL without writing any by hand. Every statement here must still pass
validate_sql(); build_examples.py checks that for each example it writes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from agent1.settings import OPERATIONS

_SCHEMA = Path(__file__).resolve().parent.parent / "config" / "schema"
ENTITIES: Dict[str, dict] = yaml.safe_load((_SCHEMA / "entities.yaml").read_text(encoding="utf-8"))["entities"]
ATTRIBUTE_TABLES: List[dict] = yaml.safe_load(
    (_SCHEMA / "attributes.yaml").read_text(encoding="utf-8"))["attribute_tables"]


def _alias(table: str) -> str:
    """state_demographics -> sd, states -> s (the style the prompt examples use)."""
    words = table.split("_")
    return "".join(w[0] for w in words) if len(words) > 1 else table[0]


def _entity(entity_type: str) -> Tuple[dict, str]:
    spec = ENTITIES[entity_type]
    return spec, _alias(spec["table"])


def _attribute_table(entity_type: str, attributes: List[str]) -> dict:
    for table in ATTRIBUTE_TABLES:
        if table["entity"] == entity_type and all(a in table["columns"] for a in attributes):
            return table
    raise ValueError(f"No attribute table for {entity_type} holds all of {attributes}")


# ── DIRECT_LOOKUP ───────────────────────────────────────────────────────────

def value_fetch(entity_type: str, attributes: List[str]) -> str:
    ent, e = _entity(entity_type)
    tab = _attribute_table(entity_type, attributes)
    d = _alias(tab["table"])
    cols = ", ".join(f"{d}.{a} AS {a}" for a in attributes)
    return (f"SELECT {e}.{ent['key_column']} AS entity_name, {d}.{tab['period_column']} AS year, {cols} "
            f"FROM {tab['table']} {d} JOIN {ent['table']} {e} ON {e}.{ent['id_column']} = {d}.{tab['join_column']} "
            f"WHERE {e}.{ent['key_column']} = ANY(:names) AND {d}.{tab['period_column']} = ANY(:years) "
            f"ORDER BY {e}.{ent['key_column']}, {d}.{tab['period_column']}")


def presence(entity_type: str, attributes: List[str]) -> str:
    ent, e = _entity(entity_type)
    tab = _attribute_table(entity_type, attributes)
    d = _alias(tab["table"])
    return (f"SELECT DISTINCT {e}.{ent['key_column']} AS entity_name "
            f"FROM {tab['table']} {d} JOIN {ent['table']} {e} ON {e}.{ent['id_column']} = {d}.{tab['join_column']} "
            f"WHERE {e}.{ent['key_column']} = ANY(:names)")


# ── GEOMETRY_LOOKUP ─────────────────────────────────────────────────────────

def shape_fetch(entity_type: str) -> str:
    ent, e = _entity(entity_type)
    geom = f"{e}.{ent['geometry_column']}"
    return (f"SELECT {e}.{ent['key_column']} AS entity_name, ST_AsText({geom}) AS wkt, ST_SRID({geom}) AS srid "
            f"FROM {ent['table']} {e} WHERE {e}.{ent['key_column']} = ANY(:names)")


# ── SPATIAL_OPERATION ───────────────────────────────────────────────────────

def operation(op: str) -> str:
    """The PostGIS function for each operation comes from config/settings.yaml."""
    return (f"SELECT ST_AsText({OPERATIONS[op]}(ST_GeomFromText(:wkt_a, :srid_a), "
            f"ST_GeomFromText(:wkt_b, :srid_b))) AS wkt")


BUFFER_WITHIN = (
    "WITH targets(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, :cand_srid) FROM unnest(CAST(:names AS text[]), "
    "CAST(:wkts AS text[])) AS t(n, w)), zone(g) AS (SELECT ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, "
    ":dist_m)::geometry) SELECT targets.entity_name AS entity_name, CASE WHEN targets.shape IS NULL THEN -1 "
    "WHEN ST_Intersects(targets.shape, zone.g) THEN 1 ELSE 0 END AS meets_zone FROM targets, zone")


# ── SPATIAL_RELATIONSHIP (adjacency / direction / distance) ─────────────────

_CANDIDATES = ("WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, :cand_srid) FROM unnest(CAST(:names AS text[]), "
               "CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid))")


def relationship(kind: str) -> str:
    if kind == "adjacency":
        return (f"{_CANDIDATES} SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref "
                f"AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)")
    if kind == "distance":
        return (f"{_CANDIDATES} SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref "
                f"AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) "
                f"ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)")
    return (f"{_CANDIDATES}, bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth("
            f"ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) "
            f"SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az BETWEEN :az_start AND :az_end "
            f"OR bearing.az + 360 BETWEEN :az_start AND :az_end ORDER BY bearing.az")


# ── SPATIAL_RELATIONSHIP_BUFFER ─────────────────────────────────────────────

ZONE = ("SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, "
        ":ref_srid AS srid")


# The area in one compass direction of a place: a wedge from its centroid
# between two bearings, the place itself removed.
SECTOR = ("WITH ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearings(a) AS (SELECT generate_se"
          "ries(CAST(:az_start AS int), CAST(:az_end AS int), 5)), arc(a, pt) AS (SELECT bearings.a, ST_Project"
          "(ST_Centroid(ref.shape)::geography, :radius_m, radians(bearings.a))::geometry FROM ref, bearings) SE"
          "LECT ST_AsText(ST_Difference(ST_MakePolygon(ST_AddPoint(ST_AddPoint(ST_MakeLine(array_agg(arc.pt ORD"
          "ER BY arc.a)), ST_Centroid(ref.shape), 0), ST_Centroid(ref.shape))), ref.shape)) AS wkt, :ref_srid A"
          "S srid FROM arc, ref GROUP BY ref.shape")


def within(entity_type: str) -> str:
    """Members of `entity_type` inside a zone: a point must lie within it, a
    line or polygon must intersect it (entities.yaml `geometry_kind`)."""
    ent, e = _entity(entity_type)
    geom = f"{e}.{ent['geometry_column']}"
    test = "ST_Within" if ent["geometry_kind"] == "point" else "ST_Intersects"
    return (f"SELECT {e}.{ent['key_column']} AS entity_name, ST_AsText({geom}) AS wkt, ST_SRID({geom}) AS srid "
            f"FROM {ent['table']} {e} WHERE {test}({geom}, "
            f"ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT ({e}.{ent['key_column']} = ANY(:exclude))")
