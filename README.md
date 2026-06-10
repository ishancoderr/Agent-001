# Multi-Agent Geospatial Missing Data System

A KQML-based multi-agent system for handling missing data in German federal-state (Bundesländer) geospatial statistics. Two autonomous agents each hold a partition of the dataset and collaborate via the KQML protocol to fulfil queries that span their combined knowledge.

---

## Overview

When a user submits a natural-language query such as:

> *"Give me population and live births for all German states from 2019 to 2023"*

the system:

1. **Parses** the query with GPT-4o mini into structured parameters
2. **Resolves** spatial relationships (adjacency, direction, distance) using PostGIS
3. **Looks up** local data and classifies every missing cell as one of three gap types
4. **Asks** the peer agent via KQML if it can fill those gaps
5. **Merges** the combined result and returns it to the user

```
User
 │
 ▼
Agent 1  (port 8000)                Agent 2  (port 8001)
 ├─ query_parser  (GPT-4o mini)      ├─ Same architecture
 ├─ spatial_validator  (PostGIS)     ├─ Holds 8 different states
 ├─ gap_detector                     └─ Responds to KQML ask
 ├─ kqml_client  ──── KQML ask ────►
 │               ◄─── KQML tell ────
 └─ merger
```

---

## Architecture

### Agents

| | Agent 1 | Agent 2 |
|---|---|---|
| Port | `8000` | `8001` |
| Database | `geostats_agent1` | `geostats_agent2` |
| States held | Bayern, Hessen, Sachsen, Thueringen, Niedersachsen, Baden-Wuert., Mecklenburg-Vorp., Sachsen-Anhalt | Berlin, Hamburg, NRW, Brandenburg, Rheinland-Pf., Saarland, Bremen, Schleswig-Holstein |

### Missing data types

| Type | Meaning | Example |
|---|---|---|
| **Attribute gap** | Row exists but some columns are NULL | Bayern married/live_births NULL 2015–2018 |
| **Temporal gap** | Year has no row for a state the agent owns | Bayern 2022+ missing |
| **Spatial gap** | State has no rows at all in this partition | NRW not in Agent 1 → ask Agent 2 |

### KQML messaging

Agents communicate using the [kqml-geo](https://github.com/ishancoderr/kqml-geo) shared package — a geo-extended KQML implementation with Pydantic validation and JSON / S-expression serialisation.

```
(ask
 :sender "Agent-1"  :receiver "Agent-2"  :reply-with "req-001"
 :language "GeoSQL"  :ontology "German-Geostats-v1"
 :content (
   :missing-slots [
     {spatial: "NRW", temporal: [2020, 2021], attributes: [population]}
   ]
 )
)
```

---

## Repository structure

```
Agent-001/
├── agent1/                   # Agent 1 FastAPI microservice
│   ├── main.py               # POST /query, POST /kqml/receive, GET /health
│   ├── query_parser.py       # NL → structured params via GPT-4o mini
│   ├── spatial_validator.py  # PostGIS: adjacency / direction / distance
│   ├── gap_detector.py       # SQL lookup + gap classification
│   ├── kqml_client.py        # Build & send KQML ask, parse tell response
│   ├── merger.py             # Combine Agent-1 + Agent-2 results
│   ├── database.py           # SQLAlchemy engine
│   ├── requirements.txt
│   ├── .env.example
│   └── test_kqml.py          # kqml-geo integration tests
│
├── db/
│   ├── schema.sql            # PostGIS tables: lands, land_stats, cities
│   ├── seed_lands.sql        # WKT geometries for all 16 Bundesländer + cities
│   └── seed_agent1.sql       # Agent 1 data partition with intentional gaps
│
└── kqml_messaging/           # Local copy / development mirror of kqml-geo
    ├── pyproject.toml
    └── kqml_messaging/
        ├── __init__.py
        └── models.py
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ with **PostGIS** extension
- Git (for installing kqml-geo from GitHub)
- OpenAI API key (for GPT-4o mini query parsing)

---

## Setup

### 1. Create the databases

```sql
-- run in psql
CREATE DATABASE geostats_agent1;
CREATE DATABASE geostats_agent2;
```

### 2. Load the schema and seed data

```bash
# Agent 1 database
psql -h localhost -p 5433 -U postgres -d geostats_agent1 -f db/schema.sql
psql -h localhost -p 5433 -U postgres -d geostats_agent1 -f db/seed_lands.sql
psql -h localhost -p 5433 -U postgres -d geostats_agent1 -f db/seed_agent1.sql

# Agent 2 database (schema + lands are the same, data partition differs)
psql -h localhost -p 5433 -U postgres -d geostats_agent2 -f db/schema.sql
psql -h localhost -p 5433 -U postgres -d geostats_agent2 -f db/seed_lands.sql
```

### 3. Configure Agent 1

```bash
cp agent1/.env.example agent1/.env
```

Edit `agent1/.env`:

```env
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASS=your_password
DB_NAME=geostats_agent1

AGENT2_URL=http://localhost:8001

OPENAI_API_KEY=sk-proj-...
```

### 4. Install dependencies

```bash
cd agent1
pip install -r requirements.txt
```

> The `kqml-geo` package is pulled directly from GitHub during install — no local copy needed.

### 5. Run Agent 1

```bash
cd agent1
uvicorn main:app --port 8000 --reload
```

---

## API endpoints

### `POST /query`

Submit a natural-language query.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Give me population for Bayern from 2019 to 2022"}'
```

**Response:**

```json
{
  "status": "partial-complete",
  "query_params": {
    "type": "DIRECT_LOOKUP",
    "spatial": ["Bayern"],
    "temporal": [2019, 2020, 2021, 2022],
    "attributes": ["population"]
  },
  "data": [
    {"state": "Bayern", "year": 2019, "population": 13124737, "source": "Agent-1"},
    {"state": "Bayern", "year": 2022, "population": 13369393, "source": "Agent-2"}
  ],
  "still_missing": [],
  "kqml_turns": 1,
  "total_records": 4
}
```

### `POST /kqml/receive`

Receives a KQML `ask` from another agent (bidirectional support).

### `GET /health`

```json
{"status": "ok", "agent": "Agent-1"}
```

---

## Supported query types

| Type | Example query |
|---|---|
| `DIRECT_LOOKUP` | *"Population of Bayern in 2021"* |
| `SPATIAL_ADJACENCY` | *"Which state borders both Hessen and Hamburg? Show population 2015–2024"* |
| `SPATIAL_DIRECTION` | *"States north of Bayern, population and married 2020–2021"* |
| `SPATIAL_DISTANCE` | *"States within 100 km of Munich, population in 2021"* |

---

## Running tests

```bash
cd agent1
python -m pytest test_kqml.py -v
```

Tests cover `MessageFactory`, JSON round-trips, `KQMLContent` status logic, and language/ontology defaults from the kqml-geo package.

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM / SQL toolkit |
| `psycopg2-binary` | PostgreSQL driver |
| `httpx` | Async HTTP client (KQML inter-agent calls) |
| `openai` | GPT-4o mini for NL query parsing |
| `python-dotenv` | Environment variable loading |
| `pydantic` | Data validation |
| `kqml-geo` | Shared KQML message models ([github.com/ishancoderr/kqml-geo](https://github.com/ishancoderr/kqml-geo)) |

---

## License

MIT
