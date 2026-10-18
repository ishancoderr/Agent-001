"""
System-wide settings from config/settings.yaml, and the ${placeholder}
rendering that keeps prompt text in step with config.

Everything here is read from config — region, default distance, relationship
kinds, direction sectors, operations, runtime limits — so no module writes one
of these values as a literal. Prompts (config/prompts/*.yaml and
config/prompts/sql/*.yaml) refer to them as ${name}; render() fills them in
when a prompt is assembled, and an unknown name is an error, not silent text.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

_CONFIG = Path(__file__).resolve().parent.parent / "config"
_SETTINGS: Dict[str, Any] = yaml.safe_load((_CONFIG / "settings.yaml").read_text(encoding="utf-8"))
_ATTRIBUTE_TABLES: List[dict] = yaml.safe_load(
    (_CONFIG / "schema" / "attributes.yaml").read_text(encoding="utf-8"))["attribute_tables"]
_ENTITIES_DOC: Dict[str, Any] = yaml.safe_load((_CONFIG / "schema" / "entities.yaml").read_text(encoding="utf-8"))

# ── Domain ───────────────────────────────────────────────────────────────────
REGION_ADJECTIVE: str = _SETTINGS["region_adjective"]
DEFAULT_DISTANCE_KM: float = float(_SETTINGS["default_distance_km"])
RELATIONSHIP_KINDS: Dict[str, List[str]] = _SETTINGS["relationship_kinds"]
DIRECTION_SECTORS: Dict[str, List[float]] = _SETTINGS["direction_sectors"]
DIRECTION_SEARCH_RADIUS_KM: float = float(_SETTINGS["direction_search_radius_km"])
PLACE_REFERENCE_KINDS: List[str] = _SETTINGS["place_reference_kinds"]
_WORDING: Dict[str, str] = _SETTINGS["relationship_wording"]
OPERATIONS: Dict[str, Any] = _SETTINGS["operations"]          # name -> PostGIS function (None: not a combine)
TOTAL_HINT_WINDOW_YEARS: int = int(_SETTINGS["total_hint_window_years"])
DATA_OPERATIONS: List[str] = _SETTINGS["data_operations"]
if not set(DATA_OPERATIONS) <= set(OPERATIONS):
    raise KeyError(f"data_operations {DATA_OPERATIONS} must be listed under operations in config/settings.yaml")

# ── Runtime ──────────────────────────────────────────────────────────────────
RUNTIME: Dict[str, Any] = _SETTINGS["runtime"]
AUTH: Dict[str, Any] = _SETTINGS["auth"]                 # login settings (agent1/auth)
EVALUATOR: Dict[str, Any] = _SETTINGS["evaluator"]       # starting it from the workbench
CONFIG_DIR: Path = _CONFIG

# ── Language models (agent1/llm/) ────────────────────────────────────────────
LLM_MODELS: Dict[str, Dict[str, Any]] = _SETTINGS["llm"]["models"]
LLM_DEFAULT: str = _SETTINGS["llm"]["default"]
OPENWEIGHT_TIMEOUT_S: float = float(_SETTINGS["llm"]["openweight_timeout_s"])
_PROVIDERS = {"openai", "anthropic", "openweight"}
for _id, _m in LLM_MODELS.items():
    if _m.get("provider") not in _PROVIDERS:
        raise KeyError(f"llm.models.{_id}: provider must be one of {sorted(_PROVIDERS)}")
if LLM_DEFAULT not in LLM_MODELS:
    raise KeyError(f"llm.default {LLM_DEFAULT!r} is not listed under llm.models")
PEER_RETRIES: int = int(RUNTIME["peer_retries"])
PEER_TIMEOUT_S: Dict[str, float] = RUNTIME["peer_timeout_s"]


def relationship_kind(query_type: str, extracted: str | None) -> str:
    """The kind a relationship query is evaluated as: the extracted kind when
    the category allows it, else the category's first kind (settings.yaml)."""
    allowed = RELATIONSHIP_KINDS[query_type]
    return extracted if extracted in allowed else allowed[0]


def relationship_wording(kind: str, distance_km: float | None) -> str:
    """How a relationship kind is named in the neutral SQL-step question
    (settings.yaml relationship_wording): "border", "lie within 100 km of",
    "lie north of"."""
    template = _WORDING.get(kind) or (_WORDING["direction"] if kind in DIRECTION_SECTORS else None)
    if template is None:
        raise KeyError(f"No relationship_wording for kind {kind!r} in config/settings.yaml")
    km = f"{distance_km:g}" if isinstance(distance_km, (int, float)) else distance_km
    return template.format(km=km, direction=kind.removesuffix("_of"))


def sector_bounds(kind: str) -> tuple[int, int]:
    """A direction's sector as (start, end) bearings in degrees, end > start:
    a sector that wraps through north ends past 360 (north_of: 315, 405).
    Bound into SQL as :az_start / :az_end."""
    start, end = DIRECTION_SECTORS[kind]
    return int(start), int(end + 360 if start > end else end)


def _default_attribute() -> str:
    """The first attribute of the default entity type's own table — what a data
    question that names no attribute is answered with."""
    entity = _ENTITIES_DOC.get("ambiguous_name_default")
    for table in _ATTRIBUTE_TABLES:
        if table["entity"] == entity:
            return next(iter(table["columns"]))
    raise KeyError(f"No attribute table for the default entity type {entity!r}")


def _quoted(names) -> str:
    return " | ".join(f'"{n}"' for n in names)


# What each ${name} in a prompt becomes.
_TOKENS: Dict[str, str] = {
    "region_adjective":    REGION_ADJECTIVE,
    "default_distance_km": f"{DEFAULT_DISTANCE_KM:g}",
    "relationship_kinds":  _quoted(k for kinds in RELATIONSHIP_KINDS.values() for k in kinds),
    "operation_names":     _quoted(OPERATIONS),
    "attribute_names":     " / ".join(c for t in _ATTRIBUTE_TABLES for c in t["columns"]),
    "default_attribute":   _default_attribute(),
    "direction_names":     _quoted(DIRECTION_SECTORS),
    "direction_sectors":   ", ".join(
        f'"{k}" {s:g}-{e:g}' if s < e else f'"{k}" {s:g}-360 or 0-{e:g}'
        for k, (s, e) in DIRECTION_SECTORS.items()),
}
_PLACEHOLDER = re.compile(r"\$\{([a-z_]+)\}")


def render(text: str) -> str:
    """Fill every ${name} in a prompt from config. An unknown name raises, so
    a typo in a prompt file fails at startup instead of reaching the model."""
    def fill(match: re.Match) -> str:
        name = match.group(1)
        if name not in _TOKENS:
            raise KeyError(f"Unknown prompt placeholder ${{{name}}} — known: {sorted(_TOKENS)}")
        return _TOKENS[name]
    return _PLACEHOLDER.sub(fill, text)
