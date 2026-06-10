# Multi-Agent Geospatial Missing Data System

A KQML-based multi-agent system for handling missing data in German federal-state (Bundesländer) geospatial statistics. Two autonomous agents each hold a partition of the dataset and collaborate via the KQML protocol to fulfil queries that span their combined knowledge.

---

## Overview

When a user submits a natural-language query such as:

> *"Give me population data from Hessen from 2022 to 2025"*

the system:

1. **Parses** the query with GPT-4o mini into structured parameters
2. **Resolves** spatial relationships (adjacency, direction, distance) using PostGIS
3. **Looks up** local data and classifies every missing cell as one of three gap types
4. **Asks** the peer agent via KQML if it can fill those gaps
5. **Merges** the combined result and returns it to the user

---

## End-to-end Request Flow

```
POST /query  {"query": "Give me population of Hessen 2022-2025"}
       │
       ▼
controller/query_controller.py  ← orchestrates all steps, logs every step
       │
       │  STEP 1 ── pipeline/query_parser.py
       │              UserQuery.query (raw English string)
       │                │
       │                ▼  GPT-4o mini
       │              QueryParams
       │                .query_type = "DIRECT_LOOKUP"
       │                .spatial    = ["Hessen"]
       │                .temporal   = [2022, 2023, 2024, 2025]
       │                .attributes = ["population"]
       │                .spatial_relationship = None
       │
       │  STEP 2 ── pipeline/spatial_validator.py
       │              DIRECT_LOOKUP → skipped entirely
       │              (for spatial queries: runs PostGIS ST_Touches /
       │               ST_Azimuth / ST_DWithin to resolve state names)
       │
       │  STEP 3 ── retrieval/gap_detector.py
       │              STEP A — Partition check SQL
       │                SELECT DISTINCT s.state_name
       │                FROM state_demographics sd
       │                JOIN states s ON s.state_id = sd.state_id
       │                WHERE s.state_name = ANY(ARRAY['Hessen'])
       │
       │                → local_states       = ["Hessen"]   (found in DB)
       │                → spatial_gap_states = []           (nothing missing)
       │
       │              STEP B — Main data lookup SQL
       │                SELECT s.state_name, sd.stat_year, sd.population
       │                FROM state_demographics sd
       │                JOIN states s ON s.state_id = sd.state_id
       │                WHERE s.state_name = ANY(ARRAY['Hessen'])
       │                  AND sd.stat_year  = ANY(ARRAY[2022,2023,2024,2025])
       │                ORDER BY s.state_name, sd.stat_year
       │
       │                Classifies each (state, year) combination:
       │                  (Hessen, 2022) row found, value present → FOUND
       │                  (Hessen, 2023) row found, value present → FOUND
       │                  (Hessen, 2024) no row at all            → TEMPORAL GAP
       │                  (Hessen, 2025) no row at all            → TEMPORAL GAP
       │
       │              returns LocalResult
       │                .found = [DataRecord(state="Hessen", year=2022,
       │                                     values={"population":6391664}),
       │                          DataRecord(state="Hessen", year=2023, ...)]
       │                .gaps  = [GapSlot(spatial=["Hessen"],
       │                                  temporal=[2024,2025],
       │                                  attributes=["population"])]
       │
       │  STEP 4 ── messaging/kqml_client.py
       │              GapSlot → MissingSlot (kqml-messaging package)
       │              MissingSlot → AskMessage (reply_with="req-001")
       │              AskMessage → JSON → POST http://localhost:8001/kqml/receive
       │
       │              Agent-2 responds with TellMessage (in_reply_to="req-001")
       │                .found_slots   = [FoundSlot with Hessen 2024, 2025 data]
       │                .missing_slots = []
       │
       │              returns {"found": [{"spatial":"Hessen","year":2024,...},
       │                                  {"spatial":"Hessen","year":2025,...}],
       │                        "missing": []}
       │
       │  STEP 5 ── result/merger.py
       │              Agent-1 DataRecord  → {"state","year","source":"Agent-1",...}
       │              Agent-2 flat dict   → {"state","year","source":"Agent-2",...}
       │                                    (renames "spatial" → "state")
       │              sorted by (state, year)
       │
       ▼
QueryResponse
  .status        = "complete"
  .query_params  = {type, spatial, temporal, attributes}
  .data          = [
      {"state":"Hessen","year":2022,"population":6391664,"source":"Agent-1"},
      {"state":"Hessen","year":2023,"population":6445000,"source":"Agent-1"},
      {"state":"Hessen","year":2024,"population":6510000,"source":"Agent-2"},
      {"state":"Hessen","year":2025,"population":6580000,"source":"Agent-2"}
    ]
  .still_missing = []
  .kqml_turns    = 1
  .total_records = 4
```

---

## Agent Architecture

```
Agent 1  (port 8000)                        Agent 2  (port 8001)
────────────────────────────────────        ────────────────────
controller/                                  Same architecture
  query_controller.py  POST /query           Holds different state partition
  kqml_controller.py   POST /kqml/receive    Responds to KQML ask
                                             Can also ask Agent-1 back
pipeline/
  query_parser.py      GPT-4o mini
  spatial_validator.py PostGIS

retrieval/
  gap_detector.py      SQL + gap classification

messaging/
  agent_registry.py    N-agent URL registry
  kqml_client.py       KQML ask/tell over HTTP
                       ──── KQML ask ────►
                       ◄─── KQML tell ───

result/
  merger.py            Combine + sort records

utils/
  show_sql.py          Dev tool: print SQL for any query

database.py            SQLAlchemy engine + SessionLocal
```

---

## Classes and Functions

### `pipeline/query_parser.py`

| Name | Type | Purpose |
|---|---|---|
| `SpatialRelationship` | dataclass | Holds relationship type, reference states, distance. e.g. `type="north_of"`, `refs=["Bayern"]` |
| `QueryParams` | dataclass | Central data object. Carries query_type, spatial list, temporal list, attributes, and optional SpatialRelationship. Passed through every layer. |
| `parse_query(query)` | function | Sends raw English to GPT-4o mini, parses JSON response into QueryParams |

### `pipeline/spatial_validator.py`

| Name | Type | Purpose |
|---|---|---|
| `validate_spatial(params)` | function | Entry point. Skips for DIRECT_LOOKUP. Routes to the correct PostGIS function. |
| `_adjacency(rel, db)` | function | Uses `ST_Touches` to find states that share a border with ALL reference states |
| `_direction(rel, db)` | function | Uses `ST_Azimuth` + angle ranges to find states in a compass direction |
| `_distance(rel, db)` | function | Uses `ST_DWithin` to find states within X km of a city |

### `retrieval/gap_detector.py`

| Name | Type | Purpose |
|---|---|---|
| `DataRecord` | dataclass | One found row: state name, year, dict of attribute values, source agent |
| `GapSlot` | dataclass | One gap: list of states, list of years, list of attributes that are missing |
| `LocalResult` | dataclass | Container for the lookup result: `found` list of DataRecord + `gaps` list of GapSlot |
| `_print_sql(label, sql, params)` | function | Prints SQL with `=` borders to terminal for copy-paste debugging |
| `execute_local_lookup(params)` | function | Two-phase SQL: STEP A partition check, STEP B data lookup. Classifies each (state, year) as found / attribute gap / temporal gap / spatial gap. Returns LocalResult. |
| `execute_local_lookup_from_slots(slot)` | function | Used when Agent-2 asks Agent-1. Runs simple lookup and returns `{found, missing}` dict. |

### `messaging/agent_registry.py`

| Name | Type | Purpose |
|---|---|---|
| `AGENT_REGISTRY` | dict | Maps agent names to URLs. Reads AGENT2_URL, AGENT3_URL, AGENT4_URL from `.env`. Add new agents without code changes. |

### `messaging/kqml_client.py`

| Name | Type | Purpose |
|---|---|---|
| `send_kqml_ask(gaps)` | function | Converts GapSlot list → MissingSlot list → AskMessage → JSON → POST to Agent-2. Parses TellMessage response back into `{found, missing}` dict. |

### `result/merger.py`

| Name | Type | Purpose |
|---|---|---|
| `merge_results(local, agent2_data)` | function | Flattens DataRecord objects and Agent-2 dicts into one unified list. Normalises field names. Sorts by (state, year). |

### `controller/query_controller.py`

| Name | Type | Purpose |
|---|---|---|
| `UserQuery` | Pydantic model | Request body. Contains `query: str`. FastAPI validates incoming JSON against this. |
| `QueryResponse` | Pydantic model | Response body. Contains status, query_params, data, still_missing, kqml_turns, total_records. |
| `handle_query(body)` | endpoint | `POST /query`. Orchestrates all 5 steps with full logging and timing. |
| `health()` | endpoint | `GET /health`. Liveness probe. |

### `controller/kqml_controller.py`

| Name | Type | Purpose |
|---|---|---|
| `KQMLMessage` | Pydantic model | Validates incoming KQML JSON body from peer agents. |
| `receive_kqml(msg)` | endpoint | `POST /kqml/receive`. Handles Agent-2's ask. Calls `execute_local_lookup_from_slots` for each slot. Returns KQML tell response. |

### `database.py`

| Name | Type | Purpose |
|---|---|---|
| `engine` | SQLAlchemy engine | Live PostgreSQL connection with `pool_pre_ping` |
| `SessionLocal` | session factory | Call `SessionLocal()` to get a database session |
| `get_db()` | generator | FastAPI dependency injection helper |

---

## Missing Data Types

| Type | Meaning | What happens |
|---|---|---|
| **Spatial gap** | State has zero rows in Agent-1's DB | Entire state → GapSlot → sent to Agent-2 |
| **Temporal gap** | State exists but no row for that year | Missing years → GapSlot → sent to Agent-2 |
| **Attribute gap** | Row exists but column value is NULL | Affected years → GapSlot → sent to Agent-2 |

---

## KQML Message Exchange

```
Agent-1                                           Agent-2
   │                                                 │
   │  POST /kqml/receive                             │
   │ ─────────────────────────────────────────────► │
   │  {                                              │
   │    "performative": "ask",                       │
   │    "sender": "Agent-1",                         │
   │    "receiver": "Agent-2",                       │
   │    "reply_with": "req-001",                     │
   │    "content": {                                 │
   │      "missing_slots": [{                        │
   │        "spatial": "Hessen",                     │
   │        "temporal": [2024, 2025],                │
   │        "attributes": ["population"]             │
   │      }]                                         │
   │    }                                            │
   │  }                                              │
   │                                                 │
   │  HTTP 200 response                              │
   │ ◄───────────────────────────────────────────── │
   │  {                                              │
   │    "performative": "tell",                      │
   │    "sender": "Agent-2",                         │
   │    "in_reply_to": "req-001",                    │
   │    "content": {                                 │
   │      "found_slots": [{                          │
   │        "spatial": "Hessen",                     │
   │        "temporal": [2024, 2025],                │
   │        "data": [                                │
   │          {"year":2024,"population":6510000},    │
   │          {"year":2025,"population":6580000}     │
   │        ]                                        │
   │      }],                                        │
   │      "missing_slots": []                        │
   │    }                                            │
   │  }                                              │
```

The shared package `kqml-messaging` (installed from [github.com/ishancoderr/kqml-geo](https://github.com/ishancoderr/kqml-geo)) provides the message classes used on both sides — `MessageFactory`, `MissingSlot`, `FoundSlot`, `AskMessage`, `TellMessage`, `JSONSerializer`.

---

## Repository Structure

```
Agent-001/
├── requirements.txt
├── README.md
│
└── agent1/
    ├── main.py                      ← FastAPI app creation + router mounting
    ├── database.py                  ← SQLAlchemy engine + SessionLocal
    ├── .env                         ← DB credentials, AGENT2_URL, OPENAI_API_KEY
    │
    ├── controller/                  ← HTTP endpoint handlers
    │   ├── query_controller.py      ← POST /query   GET /health
    │   └── kqml_controller.py       ← POST /kqml/receive
    │
    ├── pipeline/                    ← NL query understanding
    │   ├── query_parser.py          ← GPT-4o mini → QueryParams
    │   └── spatial_validator.py     ← PostGIS adjacency / direction / distance
    │
    ├── retrieval/                   ← Local DB lookup + gap detection
    │   └── gap_detector.py          ← STEP A partition check → STEP B data lookup
    │
    ├── messaging/                   ← KQML agent-to-agent communication
    │   ├── agent_registry.py        ← N-agent URL registry from .env
    │   └── kqml_client.py           ← Build ask, POST to Agent-2, parse tell
    │
    ├── result/                      ← Merge and finalize response
    │   └── merger.py
    │
    └── utils/                       ← Developer tools
        └── show_sql.py              ← Print SQL for any NL query without running it
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ with **PostGIS** extension
- OpenAI API key (GPT-4o mini)

---

## Setup

### 1. Create the database

```sql
CREATE DATABASE agent_1_db;
\c agent_1_db
CREATE EXTENSION postgis;
```

### 2. Load schema and data

```bash
psql -h localhost -p 5433 -U postgres -d agent_1_db -f db/agent1_postgis_db.sql
```

### 3. Configure environment

Edit `agent1/.env`:

```env
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASS=your_password
DB_NAME=agent_1_db

AGENT2_URL=http://localhost:8001

OPENAI_API_KEY=sk-proj-...
```

To add Agent-3 or Agent-4 later just add:
```env
AGENT3_URL=http://localhost:8002
AGENT4_URL=http://localhost:8003
```
No code changes needed.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Agent 1

```bash
cd d:\Agent-001
uvicorn agent1.main:app --port 8000 --reload
```

---

## API Endpoints

### `POST /query`

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Give me population data from Hessen from 2022 to 2025"}'
```

**Response:**

```json
{
  "status": "complete",
  "query_params": {
    "type": "DIRECT_LOOKUP",
    "spatial": ["Hessen"],
    "temporal": [2022, 2023, 2024, 2025],
    "attributes": ["population"]
  },
  "data": [
    {"state": "Hessen", "year": 2022, "population": 6391664, "source": "Agent-1"},
    {"state": "Hessen", "year": 2023, "population": 6445000, "source": "Agent-1"},
    {"state": "Hessen", "year": 2024, "population": 6510000, "source": "Agent-2"},
    {"state": "Hessen", "year": 2025, "population": 6580000, "source": "Agent-2"}
  ],
  "still_missing": [],
  "kqml_turns": 1,
  "total_records": 4
}
```

**Status values:**

| Status | Meaning |
|---|---|
| `complete` | All requested data found across agents |
| `partial-complete` | Some data found, some states still missing |
| `not-found` | No data found anywhere |

### `POST /kqml/receive`

Receives a KQML `ask` from a peer agent. Returns a KQML `tell`.

### `GET /health`

```json
{"status": "ok", "agent": "Agent-1"}
```

---

## Supported Query Types

| Type | Example |
|---|---|
| `DIRECT_LOOKUP` | `"Population of Bayern in 2021"` |
| `SPATIAL_ADJACENCY` | `"Which state borders both Hessen and Hamburg? Show population 2015-2024"` |
| `SPATIAL_DIRECTION` | `"States north of Bayern, population 2020-2021"` |
| `SPATIAL_DISTANCE` | `"States within 100 km of München, population in 2021"` |

---

## Developer Tools

Print the exact SQL that will be executed for any query — without hitting the database:

```bash
python -m agent1.utils.show_sql "Give me population for Hessen from 2022 to 2025"
```

Output:
```
============================================================
  NL Query  : Give me population for Hessen from 2022 to 2025
  Type      : DIRECT_LOOKUP
  States    : ['Hessen']
  Years     : [2022, 2023, 2024, 2025]
  Attributes: ['population']
============================================================

-- Query 1: Main data lookup
SELECT s.state_name,
       sd.stat_year,
       sd.population
FROM state_demographics sd
JOIN states s ON s.state_id = sd.state_id
WHERE s.state_name = ANY(ARRAY['Hessen'])
  AND sd.stat_year = ANY(ARRAY[2022, 2023, 2024, 2025])
ORDER BY s.state_name, sd.stat_year;

-- Query 2: Partition check
SELECT DISTINCT s.state_name
FROM state_demographics sd
JOIN states s ON s.state_id = sd.state_id
WHERE s.state_name = ANY(ARRAY['Hessen']);
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM / SQL toolkit |
| `psycopg2-binary` | PostgreSQL driver |
| `httpx` | HTTP client for KQML inter-agent calls |
| `openai` | GPT-4o mini for NL query parsing |
| `python-dotenv` | `.env` file loading |
| `pydantic` | Request/response validation |
| `kqml-messaging` | Shared KQML message models — [github.com/ishancoderr/kqml-geo](https://github.com/ishancoderr/kqml-geo) |

---

## License

MIT
