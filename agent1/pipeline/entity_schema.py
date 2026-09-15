"""
Database schema identifiers for each entity type — table name, key column,
geometry column, and (for a point entity like city) lat/lng columns — read
straight from config/schema/entities.yaml.

Before this module existed, spatial_validator.py (and, outside this
package, retrieval/geometry_resolver.py) each independently hardcoded the
same fact twice over as private ternaries ("states" if ... else "cities",
"state_name" if ... else "city_name", "geo_shape" if ... else "centroid",
...) — exactly the table/column names entities.yaml already declares, with
nothing keeping either copy in sync with it or with each other. get_schema()
is the one place SQL-building code should get a table or column name from.

These identifiers are interpolated directly into SQL text — that is no less
safe than the hardcoded Python literals it replaces, because
config/schema/entities.yaml is a developer-controlled file, never derived
from user input or a query. Query VALUES are still always bound parameters
(:name-style), never interpolated — only the identifiers (table/column
names) that SQL syntax does not allow to be bound parameters come from here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "schema"
_ENTITIES_PATH = _SCHEMA_DIR / "entities.yaml"
_ENTITIES: Dict[str, Dict[str, Any]] = yaml.safe_load(
    _ENTITIES_PATH.read_text(encoding="utf-8")
)["entities"]


def get_schema(entity_type: str) -> Dict[str, Any]:
    """Return entities.yaml's declared block for `entity_type` — table,
    key_column, id_column, geometry_column, geometry_kind, enumerable, and
    (for a point entity like city) lat_column/lng_column."""
    try:
        return _ENTITIES[entity_type]
    except KeyError:
        raise KeyError(
            f"No entity_type={entity_type!r} in config/schema/entities.yaml."
        ) from None
