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

# The eight categories a query can be classified into. Seven are answerable
# and map onto the document's scenarios; UNRELATED is the refusal.
VALID_QUERY_TYPES = {
    "DIRECT_LOOKUP", "SPATIAL_ADJACENCY", "SPATIAL_DIRECTION", "SPATIAL_DISTANCE",
    "GEOMETRY_LOOKUP", "SPATIAL_OPERATION", "SPATIAL_RELATIONSHIP_BUFFER", "UNRELATED",
}

# The three verdict relationships share one extraction template and one output
# shape (a spatial_relationship object).
RELATIONSHIP_TYPES = {"SPATIAL_ADJACENCY", "SPATIAL_DIRECTION", "SPATIAL_DISTANCE"}

# The four ways to combine two shapes, plus the named-target buffer test — see
# config/prompts/spatial_operation.yaml's own comment for why there are
# exactly five. Not sourced from config/schema: unlike VALID_ATTRS and
# VALID_ENTITY_TYPES below, no config file declares this as structured data
# (spatial_operation.yaml only mentions each name inside prose), so there is
# nothing here to deduplicate against.
VALID_OPERATIONS = {"Union", "Intersection", "Difference", "SymDifference", "BufferWithin"}

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "schema"

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
_ENTITIES = yaml.safe_load(
    (_SCHEMA_DIR / "entities.yaml").read_text(encoding="utf-8")
)["entities"]
VALID_ENTITY_TYPES = {name for name, spec in _ENTITIES.items() if spec.get("enabled", True)}


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
    # relationship genuinely could not be tested - see unknown_states.
    verdict: Optional[bool] = None
    # States a relationship query (adjacency/direction/distance) could not
    # test at all, because no geometry for them exists at either agent. Kept
    # separate from the qualifying set in `spatial`: a state absent from the
    # result because it doesn't qualify is a different fact from a state
    # absent because it could never be checked.
    unknown_states: List[str] = field(default_factory=list)
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
