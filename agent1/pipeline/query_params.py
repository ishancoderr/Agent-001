"""
The parsed form of a user query, and the vocabulary the pipeline is allowed to
produce.

Every stage of the pipeline speaks in terms of these types: the classifier
picks one of VALID_QUERY_TYPES, the extractor fills the raw fields, and
QueryParams is what the controller dispatches on. Keeping the shape here means
no stage has to import another stage just to know what a query looks like.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..settings import OPERATIONS, RELATIONSHIP_KINDS

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "schema"
_PROMPTS_DIR = _SCHEMA_DIR.parent / "prompts"

# The categories a query can be classified into — the names classify.yaml's
# own `categories:` list defines ("DIRECT_LOOKUP: asks for ..."), so the
# classifier prompt and this check can never disagree. UNRELATED is the refusal.
VALID_QUERY_TYPES = {
    entry.split(":", 1)[0].strip()
    for entry in yaml.safe_load((_PROMPTS_DIR / "classify.yaml").read_text(encoding="utf-8"))["categories"]
}

# The verdict relationships, which share one extraction template and one output
# shape (a spatial_relationship object) — config/settings.yaml relationship_kinds.
RELATIONSHIP_TYPES = set(RELATIONSHIP_KINDS)

# The four ways to combine two shapes, plus the named-target buffer test —
# config/settings.yaml `operations` (see spatial_operation.yaml for why five).
VALID_OPERATIONS = set(OPERATIONS)

# Every attribute column declared across every table in attributes.yaml — a
# query's extracted attribute names are checked against this, not a
# hardcoded {"population", "marriages", "live_births"} that would silently
# fall out of sync the moment a table there gains or loses a column.
_ATTRIBUTE_TABLES = yaml.safe_load(
    (_SCHEMA_DIR / "attributes.yaml").read_text(encoding="utf-8")
)["attribute_tables"]
VALID_ATTRS = {column for table in _ATTRIBUTE_TABLES for column in table["columns"]}

# Every enabled entity type declared in entities.yaml — same reasoning: this
# used to be a hardcoded {"city", "state"} that entities.yaml's own "adding
# an entity type needs no Python changes" promise didn't actually hold for.
_ENTITIES_DOC = yaml.safe_load((_SCHEMA_DIR / "entities.yaml").read_text(encoding="utf-8"))
_ENTITIES = _ENTITIES_DOC["entities"]
VALID_ENTITY_TYPES = {name for name, spec in _ENTITIES.items() if spec.get("enabled", True)}

# The coordinate system each type's shape column is stored in (entities.yaml
# `srid`) — used when a shape or a zone arrives without one.
ENTITY_SRID: Dict[str, int] = {name: int(_ENTITIES[name]["srid"]) for name in VALID_ENTITY_TYPES}

# The entity type assumed whenever a query doesn't determine one of its own —
# entities.yaml's own `ambiguous_name_default` (the same value gazetteer.py
# resolves an ambiguous name like "Berlin" to when a query names it without
# saying city or state). Reused here rather than a second, separately-typed
# "state" fallback: DIRECT_LOOKUP's extraction prompt has no entity_type
# field of its own yet (see config/prompts/direct_lookup.yaml), so
# agent1/retrieval/gap_detector.py falls back to this exact same config value
# instead of a Python literal, for the same reason gazetteer.py does.
DEFAULT_ENTITY_TYPE = _ENTITIES_DOC.get("ambiguous_name_default")

# The type an unlisted name (one in no closed list) is read as when the query
# doesn't say — entities.yaml's `unlisted_name_default`. Replaces the
# "anything that isn't a state is a city" literals.
UNLISTED_NAME_DEFAULT = _ENTITIES_DOC.get("unlisted_name_default")
if UNLISTED_NAME_DEFAULT not in VALID_ENTITY_TYPES:
    raise ValueError(f"entities.yaml: unlisted_name_default {UNLISTED_NAME_DEFAULT!r} is not an enabled entity type")

# Entity types whose members can be searched for inside a zone ("which cities
# lie within 30 km of X / inside the merged area of X and Y"), in entities.yaml
# order — every enabled type marked `zone_search: true`. The parser accepts
# only these as a search target, and the first one is the target when a zone
# question names none.
ZONE_SEARCH_TYPES: List[str] = [name for name, spec in _ENTITIES.items()
                                if spec.get("enabled", True) and spec.get("zone_search")]
DEFAULT_ZONE_TARGET: Optional[str] = ZONE_SEARCH_TYPES[0] if ZONE_SEARCH_TYPES else None


def entity_label(entity_type: str, plural: bool = True) -> str:
    """The wording entities.yaml gives a type ("cities", "city") — for log
    lines and generated questions, so no message spells out a type itself."""
    spec = _ENTITIES[entity_type]
    return spec["label_plural"] if plural else spec["label"]


def default_attribute_for(entity_type: str) -> str:
    """The attribute a DIRECT_LOOKUP query defaults to when it names none
    that validates — a data lookup needs at least one attribute to answer,
    but guessing which one must not mean assuming every entity's default is
    state's "population". This is the first column declared under
    `entity_type`'s own attribute table(s) in config/schema/attributes.yaml,
    so a new entity's own default comes from its own schema, not a copy of
    another entity's."""
    for table in _ATTRIBUTE_TABLES:
        if table["entity"] == entity_type:
            return next(iter(table["columns"]))
    raise KeyError(
        f"No attribute_tables entry for entity={entity_type!r} in attributes.yaml — "
        f"cannot default an attribute for an entity with no attributes at all."
    )


def _joined(items: List[str]) -> str:
    """"a, b and c" — plain English list joining, used only by
    system_capabilities_description() below."""
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def system_capabilities_description() -> str:
    """A plain-English description of what this system can answer, built
    from entities.yaml + attributes.yaml — the message shown to a user
    whose question was classified UNRELATED (see query_controller.py's
    _handle_unrelated()). Generated, not a second hand-written copy of the
    same entity/attribute list: a hardcoded copy here went stale the moment
    a new entity type was added to entities.yaml but not to this string,
    telling a user asking a legitimate question that the system couldn't
    answer it."""
    entity_labels = [spec["label_plural"] for spec in _ENTITIES.values() if spec.get("enabled", True)]
    attr_labels: List[str] = []
    seen = set()
    for table in _ATTRIBUTE_TABLES:
        for canonical, spec in table["columns"].items():
            label = spec.get("label", canonical)
            if label not in seen:
                seen.add(label)
                attr_labels.append(label)
    return (
        f"This system only answers questions about German {_joined(entity_labels)}: "
        f"data ({_joined(attr_labels)}), geometry/shape, and spatial relationships "
        f"or operations between them. Your question doesn't fit any of those "
        f"categories."
    )


@dataclass
class SpatialRelationship:
    """A relationship question: which kind, and between what.

    `subject` is what is being asked *about*; `refs` is what it is measured
    against. Its presence is what separates the two forms of the question:

        "Does Sachsen lie north of Bayern?"   subject=Sachsen, refs=[Bayern]
            -> a verdict about one named pair

        "Which states are north of Bayern?"   subject=None,    refs=[Bayern]
            -> the set of states for which the verdict holds

    Both are answered from the same computation; the subject only decides
    whether the answer is a yes/no or the set itself. Order matters, as the
    specification notes for north_of: the reference is what the bearing is
    measured from.
    """
    type: str
    refs: List[str] = field(default_factory=list)
    distance_km: Optional[float] = None
    subject: Optional[str] = None


@dataclass
class QueryParams:
    """Everything the rest of the pipeline needs to answer one query."""
    query_type: str
    spatial: List[str]
    temporal: List[int]
    attributes: List[str]
    spatial_relationship: Optional[SpatialRelationship] = None
    # Set only when the question named a subject, i.e. asked for a yes/no about
    # one pair. None means either the question asked for the set, not a
    # verdict, or the subject/reference has no geometry anywhere and the
    # relationship genuinely could not be tested - see unknown_places.
    verdict: Optional[bool] = None
    # Candidates a relationship query (adjacency/direction/distance) could not
    # test at all, because no geometry for them exists at either agent. Kept
    # separate from the qualifying set in `spatial`: a candidate absent from
    # the result because it doesn't qualify is a different fact from one
    # absent because it could never be checked.
    unknown_places: List[str] = field(default_factory=list)
    raw_query: str = ""
    # GEOMETRY_LOOKUP only
    entities: Optional[List[Dict[str, str]]] = None
    # SPATIAL_OPERATION / SPATIAL_RELATIONSHIP_BUFFER
    distance_km: Optional[float] = None
    target_entity: Optional[str] = None
    # SPATIAL_OPERATION only
    operation: Optional[str] = None
    entity_type: Optional[str] = None
    # Step-by-step trace, for evaluation logging — see metrics_logger.py
    classify_tokens: int = 0
    extract_tokens: int = 0
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    # The actual model each stage used for this request — QueryClassifier.model
    # / QueryExtractor.model, which is CLASSIFY_MODEL/EXTRACT_MODEL (the env
    # default) unless this request passed its own `model` override. Carried
    # through so evaluation logging reports what really ran, not a guess.
    classify_model: str = ""
    extract_model: str = ""
