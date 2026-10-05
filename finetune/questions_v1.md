# Fine-tuning examples — questions_v1.yaml

120 questions, 413 training examples. Generated — edit `questions_v1.yaml`, not this file.

Each step is one line of the JSONL: the model gets the linked system prompt plus **Model sees**, and is trained to reply with **Model must answer**.

# data

## d01 · DIRECT_LOOKUP

> What was the population of Hessen in 2019?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · fetch (answering Agent-1) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 5 | SQL · fetch (answering Agent-2) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
What was the population of Hessen in 2019?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What was the population of Hessen in 2019?
```

**Model must answer**

```json
{
  "spatial": ["Hessen"],
  "temporal": [2019],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "What was the population of Hessen in 2019?",
  "entity_type": "state",
  "spatial": ["Hessen"],
  "temporal": [2019],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · fetch (answering Agent-1)

*this agent answering Agent-1's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-1 asks for population of Hessen in [2019]",
  "entity_type": "state",
  "spatial": ["Hessen"],
  "temporal": [2019],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 5 · SQL · fetch (answering Agent-2)

*this agent answering Agent-2's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-2 asks for population of Hessen in [2019]",
  "entity_type": "state",
  "spatial": ["Hessen"],
  "temporal": [2019],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d02 · DIRECT_LOOKUP

> How many people lived in Sachsen and Thüringen in 2022?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
How many people lived in Sachsen and Thüringen in 2022?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: How many people lived in Sachsen and Thüringen in 2022?
```

**Model must answer**

```json
{
  "spatial": ["Sachsen", "Thüringen"],
  "temporal": [2022],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "How many people lived in Sachsen and Thüringen in 2022?",
  "entity_type": "state",
  "spatial": ["Sachsen", "Thüringen"],
  "temporal": [2022],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d03 · DIRECT_LOOKUP

> Show me the number of marriages in Niedersachsen from 2018 to 2021.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Show me the number of marriages in Niedersachsen from 2018 to 2021.
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show me the number of marriages in Niedersachsen from 2018 to 2021.
```

**Model must answer**

```json
{
  "spatial": ["Niedersachsen"],
  "temporal": [2018, 2019, 2020, 2021],
  "attributes": ["marriages"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Show me the number of marriages in Niedersachsen from 2018 to 2021.",
  "entity_type": "state",
  "spatial": ["Niedersachsen"],
  "temporal": [2018, 2019, 2020, 2021],
  "attributes": ["marriages"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.marriages AS marriages FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d04 · DIRECT_LOOKUP

> Live births in Bremen and Saarland, 2020

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · DIRECT_LOOKUP → presence | [sql_DIRECT_LOOKUP_presence.txt](prompts/sql_DIRECT_LOOKUP_presence.txt) |

### 1 · Classify

**Model sees**

```text
Live births in Bremen and Saarland, 2020
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Live births in Bremen and Saarland, 2020
```

**Model must answer**

```json
{
  "spatial": ["Bremen", "Saarland"],
  "temporal": [2020],
  "attributes": ["live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Live births in Bremen and Saarland, 2020",
  "entity_type": "state",
  "spatial": ["Bremen", "Saarland"],
  "temporal": [2020],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · DIRECT_LOOKUP → presence

*runs only when the fetch found no rows for ['Saarland']*

**Model sees**

```json
{
  "question": "Which of these state names have any row at all: ['Saarland']",
  "entity_type": "state",
  "spatial": ["Saarland"]
}
```

**Model must answer**

```sql
SELECT DISTINCT s.state_name AS entity_name FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names)
```

---

## d05 · DIRECT_LOOKUP

> Give me population, marriages and live births for Rheinland-Pfalz in 2023.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · fetch (answering Agent-1) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 5 | SQL · fetch (answering Agent-2) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Give me population, marriages and live births for Rheinland-Pfalz in 2023.
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me population, marriages and live births for Rheinland-Pfalz in 2023.
```

**Model must answer**

```json
{
  "spatial": ["Rheinland-Pfalz"],
  "temporal": [2023],
  "attributes": ["population", "marriages", "live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Give me population, marriages and live births for Rheinland-Pfalz in 2023.",
  "entity_type": "state",
  "spatial": ["Rheinland-Pfalz"],
  "temporal": [2023],
  "attributes": ["population", "marriages", "live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population, sd.marriages AS marriages, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · fetch (answering Agent-1)

*this agent answering Agent-1's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-1 asks for population, marriages, live_births of Rheinland-Pfalz in [2023]",
  "entity_type": "state",
  "spatial": ["Rheinland-Pfalz"],
  "temporal": [2023],
  "attributes": ["population", "marriages", "live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population, sd.marriages AS marriages, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 5 · SQL · fetch (answering Agent-2)

*this agent answering Agent-2's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-2 asks for population, marriages, live_births of Rheinland-Pfalz in [2023]",
  "entity_type": "state",
  "spatial": ["Rheinland-Pfalz"],
  "temporal": [2023],
  "attributes": ["population", "marriages", "live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population, sd.marriages AS marriages, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d06 · DIRECT_LOOKUP

> How many babies were born in Mecklenburg-Vorpommern in 2017?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
How many babies were born in Mecklenburg-Vorpommern in 2017?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: How many babies were born in Mecklenburg-Vorpommern in 2017?
```

**Model must answer**

```json
{
  "spatial": ["Mecklenburg-Vorpommern"],
  "temporal": [2017],
  "attributes": ["live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "How many babies were born in Mecklenburg-Vorpommern in 2017?",
  "entity_type": "state",
  "spatial": ["Mecklenburg-Vorpommern"],
  "temporal": [2017],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d07 · DIRECT_LOOKUP

> Population of every German state in 2018

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Population of every German state in 2018
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Population of every German state in 2018
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2018],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Population of every German state in 2018",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"],
  "temporal": [2018],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d08 · DIRECT_LOOKUP

> Marriages in all federal states for 2022 and 2023

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · DIRECT_LOOKUP → presence | [sql_DIRECT_LOOKUP_presence.txt](prompts/sql_DIRECT_LOOKUP_presence.txt) |

### 1 · Classify

**Model sees**

```text
Marriages in all federal states for 2022 and 2023
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Marriages in all federal states for 2022 and 2023
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2022, 2023],
  "attributes": ["marriages"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Marriages in all federal states for 2022 and 2023",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"],
  "temporal": [2022, 2023],
  "attributes": ["marriages"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.marriages AS marriages FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · DIRECT_LOOKUP → presence

*runs only when the fetch found no rows for ['Bremen', 'Saarland']*

**Model sees**

```json
{
  "question": "Which of these state names have any row at all: ['Bremen', 'Saarland']",
  "entity_type": "state",
  "spatial": ["Bremen", "Saarland"]
}
```

**Model must answer**

```sql
SELECT DISTINCT s.state_name AS entity_name FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names)
```

---

## d09 · DIRECT_LOOKUP

> Inhabitants of Baden-Wuerttemberg between 2015 and 2019

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Inhabitants of Baden-Württemberg between 2015 and 2019
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Inhabitants of Baden-Württemberg between 2015 and 2019
```

**Model must answer**

```json
{
  "spatial": ["Baden-Württemberg"],
  "temporal": [2015, 2016, 2017, 2018, 2019],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Inhabitants of Baden-Wuerttemberg between 2015 and 2019",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg"],
  "temporal": [2015, 2016, 2017, 2018, 2019],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d10 · DIRECT_LOOKUP · validation

> How many residents did Brandenburg have in 2020?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
How many residents did Brandenburg have in 2020?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: How many residents did Brandenburg have in 2020?
```

**Model must answer**

```json
{
  "spatial": ["Brandenburg"],
  "temporal": [2020],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "How many residents did Brandenburg have in 2020?",
  "entity_type": "state",
  "spatial": ["Brandenburg"],
  "temporal": [2020],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d11 · DIRECT_LOOKUP

> Number of marriages and births in Schleswig-Holstein in 2016

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Number of marriages and births in Schleswig-Holstein in 2016
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Number of marriages and births in Schleswig-Holstein in 2016
```

**Model must answer**

```json
{
  "spatial": ["Schleswig-Holstein"],
  "temporal": [2016],
  "attributes": ["marriages", "live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Number of marriages and births in Schleswig-Holstein in 2016",
  "entity_type": "state",
  "spatial": ["Schleswig-Holstein"],
  "temporal": [2016],
  "attributes": ["marriages", "live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.marriages AS marriages, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d12 · DIRECT_LOOKUP

> Compare the population of Berlin, Hamburg and Bremen in 2020

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · DIRECT_LOOKUP → presence | [sql_DIRECT_LOOKUP_presence.txt](prompts/sql_DIRECT_LOOKUP_presence.txt) |
| 5 | SQL · fetch (answering Agent-1) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 6 | SQL · fetch (answering Agent-2) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Compare the population of Berlin, Hamburg and Bremen in 2020
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Compare the population of Berlin, Hamburg and Bremen in 2020
```

**Model must answer**

```json
{
  "spatial": ["Berlin", "Hamburg", "Bremen"],
  "temporal": [2020],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Compare the population of Berlin, Hamburg and Bremen in 2020",
  "entity_type": "state",
  "spatial": ["Berlin", "Hamburg", "Bremen"],
  "temporal": [2020],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · DIRECT_LOOKUP → presence

*runs only when the fetch found no rows for ['Bremen']*

**Model sees**

```json
{
  "question": "Which of these state names have any row at all: ['Bremen']",
  "entity_type": "state",
  "spatial": ["Bremen"]
}
```

**Model must answer**

```sql
SELECT DISTINCT s.state_name AS entity_name FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names)
```

### 5 · SQL · fetch (answering Agent-1)

*this agent answering Agent-1's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-1 asks for population of Berlin, Hamburg, Bremen in [2020]",
  "entity_type": "state",
  "spatial": ["Berlin", "Hamburg", "Bremen"],
  "temporal": [2020],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 6 · SQL · fetch (answering Agent-2)

*this agent answering Agent-2's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-2 asks for population of Berlin, Hamburg, Bremen in [2020]",
  "entity_type": "state",
  "spatial": ["Berlin", "Hamburg", "Bremen"],
  "temporal": [2020],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d13 · DIRECT_LOOKUP

> nordrhein westfalen population 2024

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Nordrhein-Westfalen population 2024
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Nordrhein-Westfalen population 2024
```

**Model must answer**

```json
{
  "spatial": ["Nordrhein-Westfalen"],
  "temporal": [2024],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "nordrhein westfalen population 2024",
  "entity_type": "state",
  "spatial": ["Nordrhein-Westfalen"],
  "temporal": [2024],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d14 · DIRECT_LOOKUP

> What were the live births in Sachsen-Anhalt in 2019 and 2021?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
What were the live births in Sachsen-Anhalt in 2019 and 2021?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What were the live births in Sachsen-Anhalt in 2019 and 2021?
```

**Model must answer**

```json
{
  "spatial": ["Sachsen-Anhalt"],
  "temporal": [2019, 2021],
  "attributes": ["live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "What were the live births in Sachsen-Anhalt in 2019 and 2021?",
  "entity_type": "state",
  "spatial": ["Sachsen-Anhalt"],
  "temporal": [2019, 2021],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d15 · DIRECT_LOOKUP

> Population and marriages for Bayern and Baden-Württemberg, 2014-2016

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Population and marriages for Bayern and Baden-Württemberg, 2014-2016
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Population and marriages for Bayern and Baden-Württemberg, 2014-2016
```

**Model must answer**

```json
{
  "spatial": ["Bayern", "Baden-Württemberg"],
  "temporal": [2014, 2015, 2016],
  "attributes": ["population", "marriages"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Population and marriages for Bayern and Baden-Württemberg, 2014-2016",
  "entity_type": "state",
  "spatial": ["Bayern", "Baden-Württemberg"],
  "temporal": [2014, 2015, 2016],
  "attributes": ["population", "marriages"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population, sd.marriages AS marriages FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d16 · DIRECT_LOOKUP

> How many couples got married in Hessen in 2023?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
How many couples got married in Hessen in 2023?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: How many couples got married in Hessen in 2023?
```

**Model must answer**

```json
{
  "spatial": ["Hessen"],
  "temporal": [2023],
  "attributes": ["marriages"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "How many couples got married in Hessen in 2023?",
  "entity_type": "state",
  "spatial": ["Hessen"],
  "temporal": [2023],
  "attributes": ["marriages"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.marriages AS marriages FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d17 · DIRECT_LOOKUP

> Tell me the population figures for Thüringen, Sachsen and Sachsen-Anhalt in 2020.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · DIRECT_LOOKUP → presence | [sql_DIRECT_LOOKUP_presence.txt](prompts/sql_DIRECT_LOOKUP_presence.txt) |

### 1 · Classify

**Model sees**

```text
Tell me the population figures for Thüringen, Sachsen and Sachsen-Anhalt in 2020.
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Tell me the population figures for Thüringen, Sachsen and Sachsen-Anhalt in 2020.
```

**Model must answer**

```json
{
  "spatial": ["Thüringen", "Sachsen", "Sachsen-Anhalt"],
  "temporal": [2020],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Tell me the population figures for Thüringen, Sachsen and Sachsen-Anhalt in 2020.",
  "entity_type": "state",
  "spatial": ["Thüringen", "Sachsen", "Sachsen-Anhalt"],
  "temporal": [2020],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · DIRECT_LOOKUP → presence

*runs only when the fetch found no rows for ['Sachsen-Anhalt']*

**Model sees**

```json
{
  "question": "Which of these state names have any row at all: ['Sachsen-Anhalt']",
  "entity_type": "state",
  "spatial": ["Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT DISTINCT s.state_name AS entity_name FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names)
```

---

## d18 · DIRECT_LOOKUP

> Bavaria population in 2022

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Bavaria population in 2022
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Bavaria population in 2022
```

**Model must answer**

```json
{
  "spatial": ["Bayern"],
  "temporal": [2022],
  "attributes": ["population"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Bavaria population in 2022",
  "entity_type": "state",
  "spatial": ["Bayern"],
  "temporal": [2022],
  "attributes": ["population"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.population AS population FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d19 · DIRECT_LOOKUP

> How many marriages were registered in Lower Saxony in 2019?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
How many marriages were registered in Lower Saxony in 2019?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: How many marriages were registered in Lower Saxony in 2019?
```

**Model must answer**

```json
{
  "spatial": ["Niedersachsen"],
  "temporal": [2019],
  "attributes": ["marriages"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "How many marriages were registered in Lower Saxony in 2019?",
  "entity_type": "state",
  "spatial": ["Niedersachsen"],
  "temporal": [2019],
  "attributes": ["marriages"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.marriages AS marriages FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d20 · DIRECT_LOOKUP · validation

> Live birth data for Hamburg and Schleswig-Holstein from 2021 to 2024

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |
| 3 | SQL · DIRECT_LOOKUP → fetch | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 4 | SQL · fetch (answering Agent-1) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |
| 5 | SQL · fetch (answering Agent-2) | [sql_DIRECT_LOOKUP_fetch.txt](prompts/sql_DIRECT_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Live birth data for Hamburg and Schleswig-Holstein from 2021 to 2024
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Live birth data for Hamburg and Schleswig-Holstein from 2021 to 2024
```

**Model must answer**

```json
{
  "spatial": ["Hamburg", "Schleswig-Holstein"],
  "temporal": [2021, 2022, 2023, 2024],
  "attributes": ["live_births"],
  "entity_type": "state"
}
```

### 3 · SQL · DIRECT_LOOKUP → fetch

**Model sees**

```json
{
  "question": "Live birth data for Hamburg and Schleswig-Holstein from 2021 to 2024",
  "entity_type": "state",
  "spatial": ["Hamburg", "Schleswig-Holstein"],
  "temporal": [2021, 2022, 2023, 2024],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 4 · SQL · fetch (answering Agent-1)

*this agent answering Agent-1's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-1 asks for live_births of Hamburg, Schleswig-Holstein in [2021, 2022, 2023, 2024]",
  "entity_type": "state",
  "spatial": ["Hamburg", "Schleswig-Holstein"],
  "temporal": [2021, 2022, 2023, 2024],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

### 5 · SQL · fetch (answering Agent-2)

*this agent answering Agent-2's :missing-slots ask*

**Model sees**

```json
{
  "question": "Agent-2 asks for live_births of Hamburg, Schleswig-Holstein in [2021, 2022, 2023, 2024]",
  "entity_type": "state",
  "spatial": ["Hamburg", "Schleswig-Holstein"],
  "temporal": [2021, 2022, 2023, 2024],
  "attributes": ["live_births"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, sd.stat_year AS year, sd.live_births AS live_births FROM state_demographics sd JOIN states s ON s.state_id = sd.state_id WHERE s.state_name = ANY(:names) AND sd.stat_year = ANY(:years) ORDER BY s.state_name, sd.stat_year
```

---

## d21 · DIRECT_LOOKUP

> What is the population of Sachsen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |

### 1 · Classify

**Model sees**

```text
What is the population of Sachsen?
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What is the population of Sachsen?
```

**Model must answer**

```json
{
  "spatial": ["Sachsen"],
  "temporal": [],
  "attributes": ["population"],
  "entity_type": "state"
}
```

---

## d22 · DIRECT_LOOKUP

> Show marriage numbers for Bremen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_DIRECT_LOOKUP.txt](prompts/extract_DIRECT_LOOKUP.txt) |

### 1 · Classify

**Model sees**

```text
Show marriage numbers for Bremen
```

**Model must answer**

```json
{"query_type": "DIRECT_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show marriage numbers for Bremen
```

**Model must answer**

```json
{
  "spatial": ["Bremen"],
  "temporal": [],
  "attributes": ["marriages"],
  "entity_type": "state"
}
```

---

# geometry

## g01 · GEOMETRY_LOOKUP

> Show the boundary of Hessen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Show the boundary of Hessen
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show the boundary of Hessen
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Hessen", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hessen']",
  "entity_type": "state",
  "spatial": ["Hessen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g02 · GEOMETRY_LOOKUP

> What is the shape of Thüringen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
What is the shape of Thüringen?
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What is the shape of Thüringen?
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Thüringen", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Thüringen']",
  "entity_type": "state",
  "spatial": ["Thüringen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g03 · GEOMETRY_LOOKUP

> Give me the geometry of Köln

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Give me the geometry of Cologne
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me the geometry of Cologne
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Cologne", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Cologne']",
  "entity_type": "city",
  "spatial": ["Cologne"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g04 · GEOMETRY_LOOKUP

> Where is Leipzig located? Give me its coordinates.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Where is Leipzig located? Give me its coordinates.
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Where is Leipzig located? Give me its coordinates.
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Leipzig", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Leipzig']",
  "entity_type": "city",
  "spatial": ["Leipzig"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g05 · GEOMETRY_LOOKUP

> WKT for Niedersachsen and Bremen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
WKT for Niedersachsen and Bremen
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: WKT for Niedersachsen and Bremen
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Niedersachsen", "entity_type": "state"}, {"entity_name": "Bremen", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Bremen', 'Niedersachsen']",
  "entity_type": "state",
  "spatial": ["Bremen", "Niedersachsen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g06 · GEOMETRY_LOOKUP

> Show me the outline of Mecklenburg-Vorpommern

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Show me the outline of Mecklenburg-Vorpommern
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show me the outline of Mecklenburg-Vorpommern
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Mecklenburg-Vorpommern", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Mecklenburg-Vorpommern']",
  "entity_type": "state",
  "spatial": ["Mecklenburg-Vorpommern"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g07 · GEOMETRY_LOOKUP

> What are the coordinates of Dresden and Erfurt?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
What are the coordinates of Dresden and Erfurt?
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What are the coordinates of Dresden and Erfurt?
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Dresden", "entity_type": "city"}, {"entity_name": "Erfurt", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Dresden', 'Erfurt']",
  "entity_type": "city",
  "spatial": ["Dresden", "Erfurt"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g08 · GEOMETRY_LOOKUP

> Geometry of the city of Hamburg

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Geometry of the city of Hamburg
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Geometry of the city of Hamburg
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Hamburg", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Hamburg']",
  "entity_type": "city",
  "spatial": ["Hamburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g09 · GEOMETRY_LOOKUP

> Give me the polygons of Saarland and Rheinland-Pfalz

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Give me the polygons of Saarland and Rheinland-Pfalz
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me the polygons of Saarland and Rheinland-Pfalz
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Saarland", "entity_type": "state"}, {"entity_name": "Rheinland-Pfalz", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Rheinland-Pfalz', 'Saarland']",
  "entity_type": "state",
  "spatial": ["Rheinland-Pfalz", "Saarland"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g10 · GEOMETRY_LOOKUP · validation

> Point location of Stuttgart

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |

### 1 · Classify

**Model sees**

```text
Point location of Stuttgart
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Point location of Stuttgart
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Stuttgart", "entity_type": "city"}]
}
```

---

## g11 · GEOMETRY_LOOKUP

> Boundaries of Brandenburg, Berlin and Sachsen-Anhalt

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Boundaries of Brandenburg, Berlin and Sachsen-Anhalt
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Boundaries of Brandenburg, Berlin and Sachsen-Anhalt
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Brandenburg", "entity_type": "state"}, {"entity_name": "Berlin", "entity_type": "state"}, {"entity_name": "Sachsen-Anhalt", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Berlin', 'Brandenburg', 'Sachsen-Anhalt']",
  "entity_type": "state",
  "spatial": ["Berlin", "Brandenburg", "Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g12 · GEOMETRY_LOOKUP

> Show the centroid of Frankfurt

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Show the centroid of Frankfurt
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show the centroid of Frankfurt
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Frankfurt", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Frankfurt']",
  "entity_type": "city",
  "spatial": ["Frankfurt"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g13 · GEOMETRY_LOOKUP

> geometry of muenchen and nuernberg

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
geometry of Munich and Nuremberg
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: geometry of Munich and Nuremberg
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Munich", "entity_type": "city"}, {"entity_name": "Nuremberg", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Munich', 'Nuremberg']",
  "entity_type": "city",
  "spatial": ["Munich", "Nuremberg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g14 · GEOMETRY_LOOKUP

> Give me the shapes of Hessen and Kassel

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Give me the shapes of Hessen and Kassel
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me the shapes of Hessen and Kassel
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Hessen", "entity_type": "state"}, {"entity_name": "Kassel", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Kassel']",
  "entity_type": "city",
  "spatial": ["Kassel"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g15 · GEOMETRY_LOOKUP

> Map the border of Schleswig-Holstein

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Map the border of Schleswig-Holstein
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Map the border of Schleswig-Holstein
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Schleswig-Holstein", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Schleswig-Holstein']",
  "entity_type": "state",
  "spatial": ["Schleswig-Holstein"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g16 · GEOMETRY_LOOKUP

> What does the boundary of Baden-Württemberg look like as WKT?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
What does the boundary of Baden-Württemberg look like as WKT?
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: What does the boundary of Baden-Württemberg look like as WKT?
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Baden-Württemberg", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Baden-Württemberg']",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g17 · GEOMETRY_LOOKUP

> Coordinates of Hannover, the city of Bremen and Kiel

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Coordinates of Hannover, the city of Bremen and Kiel
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Coordinates of Hannover, the city of Bremen and Kiel
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Hannover", "entity_type": "city"}, {"entity_name": "Bremen", "entity_type": "city"}, {"entity_name": "Kiel", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Bremen', 'Hannover', 'Kiel']",
  "entity_type": "city",
  "spatial": ["Bremen", "Hannover", "Kiel"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g18 · GEOMETRY_LOOKUP

> Return the geometry for Nordrhein-Westfalen, Düsseldorf and Dortmund

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Return the geometry for Nordrhein-Westfalen, Düsseldorf and Dortmund
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Return the geometry for Nordrhein-Westfalen, Düsseldorf and Dortmund
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Nordrhein-Westfalen", "entity_type": "state"}, {"entity_name": "Düsseldorf", "entity_type": "city"}, {"entity_name": "Dortmund", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Nordrhein-Westfalen']",
  "entity_type": "state",
  "spatial": ["Nordrhein-Westfalen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Dortmund', 'Düsseldorf']",
  "entity_type": "city",
  "spatial": ["Dortmund", "Düsseldorf"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

## g19 · GEOMETRY_LOOKUP

> Show shapes of Sachsen and Thüringen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Show shapes of Sachsen and Thüringen
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Show shapes of Sachsen and Thüringen
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Sachsen", "entity_type": "state"}, {"entity_name": "Thüringen", "entity_type": "state"}]
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Sachsen', 'Thüringen']",
  "entity_type": "state",
  "spatial": ["Sachsen", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

---

## g20 · GEOMETRY_LOOKUP · validation

> Where exactly is Magdeburg? I need its point geometry.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |

### 1 · Classify

**Model sees**

```text
Where exactly is Magdeburg? I need its point geometry.
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Where exactly is Magdeburg? I need its point geometry.
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Magdeburg", "entity_type": "city"}]
}
```

---

## g21 · GEOMETRY_LOOKUP

> Give me the boundary of Hesse

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |

### 1 · Classify

**Model sees**

```text
Give me the boundary of Hesse
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me the boundary of Hesse
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Hessen", "entity_type": "state"}]
}
```

---

## g22 · GEOMETRY_LOOKUP

> Shape of Rostock and Potsdam

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_GEOMETRY_LOOKUP.txt](prompts/extract_GEOMETRY_LOOKUP.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |

### 1 · Classify

**Model sees**

```text
Shape of Rostock and Potsdam
```

**Model must answer**

```json
{"query_type": "GEOMETRY_LOOKUP"}
```

### 2 · Extract

**Model sees**

```text
Query: Shape of Rostock and Potsdam
```

**Model must answer**

```json
{
  "entities": [{"entity_name": "Rostock", "entity_type": "city"}, {"entity_name": "Potsdam", "entity_type": "city"}]
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Potsdam', 'Rostock']",
  "entity_type": "city",
  "spatial": ["Potsdam", "Rostock"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

---

# operation

## o01 · SPATIAL_OPERATION

> Combine Hessen and Thüringen into one boundary

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Combine Hessen and Thüringen into one boundary
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Combine Hessen and Thüringen into one boundary
```

**Model must answer**

```json
{
  "operation": "Union",
  "spatial": ["Hessen", "Thüringen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hessen', 'Thüringen']",
  "entity_type": "state",
  "spatial": ["Hessen", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Combine Hessen and Thüringen into one boundary",
  "operation": "Union",
  "spatial": ["Hessen", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Union(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o02 · SPATIAL_OPERATION

> Merge Niedersachsen and Bremen into a single shape

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Merge Niedersachsen and Bremen into a single shape
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Merge Niedersachsen and Bremen into a single shape
```

**Model must answer**

```json
{
  "operation": "Union",
  "spatial": ["Niedersachsen", "Bremen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Merge Niedersachsen and Bremen into a single shape",
  "operation": "Union",
  "spatial": ["Niedersachsen", "Bremen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Union(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o03 · SPATIAL_OPERATION

> What is the union of Rheinland-Pfalz and Saarland?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
What is the union of Rheinland-Pfalz and Saarland?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: What is the union of Rheinland-Pfalz and Saarland?
```

**Model must answer**

```json
{
  "operation": "Union",
  "spatial": ["Rheinland-Pfalz", "Saarland"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "What is the union of Rheinland-Pfalz and Saarland?",
  "operation": "Union",
  "spatial": ["Rheinland-Pfalz", "Saarland"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Union(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o04 · SPATIAL_OPERATION

> One combined area for Sachsen, Sachsen-Anhalt and Thüringen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
One combined area for Sachsen, Sachsen-Anhalt and Thüringen
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: One combined area for Sachsen, Sachsen-Anhalt and Thüringen
```

**Model must answer**

```json
{
  "operation": "Union",
  "spatial": ["Sachsen", "Sachsen-Anhalt", "Thüringen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Sachsen', 'Sachsen-Anhalt', 'Thüringen']",
  "entity_type": "state",
  "spatial": ["Sachsen", "Sachsen-Anhalt", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "One combined area for Sachsen, Sachsen-Anhalt and Thüringen",
  "operation": "Union",
  "spatial": ["Sachsen", "Sachsen-Anhalt", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Union(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o05 · SPATIAL_OPERATION

> Join Berlin and Brandenburg into one polygon

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Join Berlin and Brandenburg into one polygon
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Join Berlin and Brandenburg into one polygon
```

**Model must answer**

```json
{
  "operation": "Union",
  "spatial": ["Berlin", "Brandenburg"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Berlin', 'Brandenburg']",
  "entity_type": "state",
  "spatial": ["Berlin", "Brandenburg"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Join Berlin and Brandenburg into one polygon",
  "operation": "Union",
  "spatial": ["Berlin", "Brandenburg"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Union(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o06 · SPATIAL_OPERATION

> What area do Hessen and Bayern have in common?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
What area do Hessen and Bayern have in common?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: What area do Hessen and Bayern have in common?
```

**Model must answer**

```json
{
  "operation": "Intersection",
  "spatial": ["Hessen", "Bayern"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Bayern', 'Hessen']",
  "entity_type": "state",
  "spatial": ["Bayern", "Hessen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "What area do Hessen and Bayern have in common?",
  "operation": "Intersection",
  "spatial": ["Hessen", "Bayern"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Intersection(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o07 · SPATIAL_OPERATION

> Intersection of Nordrhein-Westfalen and Niedersachsen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Intersection of Nordrhein-Westfalen and Niedersachsen
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Intersection of Nordrhein-Westfalen and Niedersachsen
```

**Model must answer**

```json
{
  "operation": "Intersection",
  "spatial": ["Nordrhein-Westfalen", "Niedersachsen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Niedersachsen', 'Nordrhein-Westfalen']",
  "entity_type": "state",
  "spatial": ["Niedersachsen", "Nordrhein-Westfalen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Intersection of Nordrhein-Westfalen and Niedersachsen",
  "operation": "Intersection",
  "spatial": ["Nordrhein-Westfalen", "Niedersachsen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Intersection(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o08 · SPATIAL_OPERATION

> Which region is shared by Brandenburg and Mecklenburg-Vorpommern?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which region is shared by Brandenburg and Mecklenburg-Vorpommern?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which region is shared by Brandenburg and Mecklenburg-Vorpommern?
```

**Model must answer**

```json
{
  "operation": "Intersection",
  "spatial": ["Brandenburg", "Mecklenburg-Vorpommern"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Brandenburg', 'Mecklenburg-Vorpommern']",
  "entity_type": "state",
  "spatial": ["Brandenburg", "Mecklenburg-Vorpommern"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Which region is shared by Brandenburg and Mecklenburg-Vorpommern?",
  "operation": "Intersection",
  "spatial": ["Brandenburg", "Mecklenburg-Vorpommern"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Intersection(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o09 · SPATIAL_OPERATION

> Overlap between Baden-Württemberg and Rheinland-Pfalz

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Overlap between Baden-Württemberg and Rheinland-Pfalz
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Overlap between Baden-Württemberg and Rheinland-Pfalz
```

**Model must answer**

```json
{
  "operation": "Intersection",
  "spatial": ["Baden-Württemberg", "Rheinland-Pfalz"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Baden-Württemberg', 'Rheinland-Pfalz']",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg", "Rheinland-Pfalz"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Overlap between Baden-Württemberg and Rheinland-Pfalz",
  "operation": "Intersection",
  "spatial": ["Baden-Württemberg", "Rheinland-Pfalz"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Intersection(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o10 · SPATIAL_OPERATION · validation

> Niedersachsen without Bremen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Niedersachsen without Bremen
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Niedersachsen without Bremen
```

**Model must answer**

```json
{
  "operation": "Difference",
  "spatial": ["Niedersachsen", "Bremen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Niedersachsen without Bremen",
  "operation": "Difference",
  "spatial": ["Niedersachsen", "Bremen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Difference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o11 · SPATIAL_OPERATION

> Remove Hamburg from Schleswig-Holstein

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Remove Hamburg from Schleswig-Holstein
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Remove Hamburg from Schleswig-Holstein
```

**Model must answer**

```json
{
  "operation": "Difference",
  "spatial": ["Schleswig-Holstein", "Hamburg"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hamburg', 'Schleswig-Holstein']",
  "entity_type": "state",
  "spatial": ["Hamburg", "Schleswig-Holstein"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Remove Hamburg from Schleswig-Holstein",
  "operation": "Difference",
  "spatial": ["Schleswig-Holstein", "Hamburg"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Difference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o12 · SPATIAL_OPERATION

> Show Bayern minus Baden-Württemberg

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Show Bayern minus Baden-Württemberg
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Show Bayern minus Baden-Württemberg
```

**Model must answer**

```json
{
  "operation": "Difference",
  "spatial": ["Bayern", "Baden-Württemberg"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Baden-Württemberg', 'Bayern']",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg", "Bayern"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Show Bayern minus Baden-Württemberg",
  "operation": "Difference",
  "spatial": ["Bayern", "Baden-Württemberg"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Difference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o13 · SPATIAL_OPERATION

> Hessen with Thüringen cut out

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Hessen with Thüringen cut out
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Hessen with Thüringen cut out
```

**Model must answer**

```json
{
  "operation": "Difference",
  "spatial": ["Hessen", "Thüringen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Hessen with Thüringen cut out",
  "operation": "Difference",
  "spatial": ["Hessen", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Difference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o14 · SPATIAL_OPERATION

> What is left of Sachsen once Sachsen-Anhalt is taken away?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
What is left of Sachsen once Sachsen-Anhalt is taken away?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: What is left of Sachsen once Sachsen-Anhalt is taken away?
```

**Model must answer**

```json
{
  "operation": "Difference",
  "spatial": ["Sachsen", "Sachsen-Anhalt"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Sachsen', 'Sachsen-Anhalt']",
  "entity_type": "state",
  "spatial": ["Sachsen", "Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "What is left of Sachsen once Sachsen-Anhalt is taken away?",
  "operation": "Difference",
  "spatial": ["Sachsen", "Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Difference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o15 · SPATIAL_OPERATION

> Areas in Hessen or Rheinland-Pfalz but not in both

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Areas in Hessen or Rheinland-Pfalz but not in both
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Areas in Hessen or Rheinland-Pfalz but not in both
```

**Model must answer**

```json
{
  "operation": "SymDifference",
  "spatial": ["Hessen", "Rheinland-Pfalz"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hessen', 'Rheinland-Pfalz']",
  "entity_type": "state",
  "spatial": ["Hessen", "Rheinland-Pfalz"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Areas in Hessen or Rheinland-Pfalz but not in both",
  "operation": "SymDifference",
  "spatial": ["Hessen", "Rheinland-Pfalz"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_SymDifference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o16 · SPATIAL_OPERATION

> Symmetric difference of Thüringen and Sachsen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Symmetric difference of Thüringen and Sachsen
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Symmetric difference of Thüringen and Sachsen
```

**Model must answer**

```json
{
  "operation": "SymDifference",
  "spatial": ["Thüringen", "Sachsen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Symmetric difference of Thüringen and Sachsen",
  "operation": "SymDifference",
  "spatial": ["Thüringen", "Sachsen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_SymDifference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o17 · SPATIAL_OPERATION

> Which parts belong to exactly one of Niedersachsen and Nordrhein-Westfalen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which parts belong to exactly one of Niedersachsen and Nordrhein-Westfalen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which parts belong to exactly one of Niedersachsen and Nordrhein-Westfalen?
```

**Model must answer**

```json
{
  "operation": "SymDifference",
  "spatial": ["Niedersachsen", "Nordrhein-Westfalen"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Which parts belong to exactly one of Niedersachsen and Nordrhein-Westfalen?",
  "operation": "SymDifference",
  "spatial": ["Niedersachsen", "Nordrhein-Westfalen"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_SymDifference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o18 · SPATIAL_OPERATION

> Give me the symmetric difference between Brandenburg and Sachsen-Anhalt

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → compute | [sql_SPATIAL_OPERATION_compute.txt](prompts/sql_SPATIAL_OPERATION_compute.txt) |

### 1 · Classify

**Model sees**

```text
Give me the symmetric difference between Brandenburg and Sachsen-Anhalt
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me the symmetric difference between Brandenburg and Sachsen-Anhalt
```

**Model must answer**

```json
{
  "operation": "SymDifference",
  "spatial": ["Brandenburg", "Sachsen-Anhalt"],
  "entity_type": "state",
  "distance_km": null
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Brandenburg', 'Sachsen-Anhalt']",
  "entity_type": "state",
  "spatial": ["Brandenburg", "Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → compute

**Model sees**

```json
{
  "question": "Give me the symmetric difference between Brandenburg and Sachsen-Anhalt",
  "operation": "SymDifference",
  "spatial": ["Brandenburg", "Sachsen-Anhalt"]
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_SymDifference(ST_GeomFromText(:wkt_a, :srid_a), ST_GeomFromText(:wkt_b, :srid_b))) AS wkt
```

---

## o19 · SPATIAL_OPERATION

> Which of Hessen and Thüringen lie within 80 km of Frankfurt?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → buffer_within | [sql_SPATIAL_OPERATION_buffer_within.txt](prompts/sql_SPATIAL_OPERATION_buffer_within.txt) |

### 1 · Classify

**Model sees**

```text
Which of Hessen and Thüringen lie within 80 km of Frankfurt?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which of Hessen and Thüringen lie within 80 km of Frankfurt?
```

**Model must answer**

```json
{
  "operation": "BufferWithin",
  "spatial": ["Frankfurt", "Hessen", "Thüringen"],
  "entity_type": "state",
  "distance_km": 80
}
```

### 3 · SQL · SPATIAL_OPERATION → buffer_within

**Model sees**

```json
{
  "question": "Which of Hessen and Thüringen lie within 80 km of Frankfurt?",
  "operation": "BufferWithin",
  "spatial": ["Frankfurt", "Hessen", "Thüringen"],
  "distance_km": 80.0
}
```

**Model must answer**

```sql
WITH targets(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), zone(g) AS (SELECT ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) SELECT targets.entity_name AS entity_name, CASE WHEN targets.shape IS NULL THEN -1 WHEN ST_Intersects(targets.shape, zone.g) THEN 1 ELSE 0 END AS meets_zone FROM targets, zone
```

---

## o20 · SPATIAL_OPERATION · validation

> Which of Sachsen and Brandenburg lie within 50 km of Leipzig?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · SPATIAL_OPERATION → buffer_within | [sql_SPATIAL_OPERATION_buffer_within.txt](prompts/sql_SPATIAL_OPERATION_buffer_within.txt) |

### 1 · Classify

**Model sees**

```text
Which of Sachsen and Brandenburg lie within 50 km of Leipzig?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which of Sachsen and Brandenburg lie within 50 km of Leipzig?
```

**Model must answer**

```json
{
  "operation": "BufferWithin",
  "spatial": ["Leipzig", "Sachsen", "Brandenburg"],
  "entity_type": "state",
  "distance_km": 50
}
```

### 3 · SQL · SPATIAL_OPERATION → buffer_within

**Model sees**

```json
{
  "question": "Which of Sachsen and Brandenburg lie within 50 km of Leipzig?",
  "operation": "BufferWithin",
  "spatial": ["Leipzig", "Sachsen", "Brandenburg"],
  "distance_km": 50.0
}
```

**Model must answer**

```sql
WITH targets(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), zone(g) AS (SELECT ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) SELECT targets.entity_name AS entity_name, CASE WHEN targets.shape IS NULL THEN -1 WHEN ST_Intersects(targets.shape, zone.g) THEN 1 ELSE 0 END AS meets_zone FROM targets, zone
```

---

## o21 · SPATIAL_OPERATION

> Of Bayern and Baden-Württemberg, which are within 120 km of Stuttgart?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_OPERATION → buffer_within | [sql_SPATIAL_OPERATION_buffer_within.txt](prompts/sql_SPATIAL_OPERATION_buffer_within.txt) |

### 1 · Classify

**Model sees**

```text
Of Bayern and Baden-Württemberg, which are within 120 km of Stuttgart?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Of Bayern and Baden-Württemberg, which are within 120 km of Stuttgart?
```

**Model must answer**

```json
{
  "operation": "BufferWithin",
  "spatial": ["Stuttgart", "Bayern", "Baden-Württemberg"],
  "entity_type": "state",
  "distance_km": 120
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Stuttgart']",
  "entity_type": "city",
  "spatial": ["Stuttgart"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_OPERATION → buffer_within

**Model sees**

```json
{
  "question": "Of Bayern and Baden-Württemberg, which are within 120 km of Stuttgart?",
  "operation": "BufferWithin",
  "spatial": ["Stuttgart", "Bayern", "Baden-Württemberg"],
  "distance_km": 120.0
}
```

**Model must answer**

```sql
WITH targets(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), zone(g) AS (SELECT ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) SELECT targets.entity_name AS entity_name, CASE WHEN targets.shape IS NULL THEN -1 WHEN ST_Intersects(targets.shape, zone.g) THEN 1 ELSE 0 END AS meets_zone FROM targets, zone
```

---

## o22 · SPATIAL_OPERATION

> Which of Mecklenburg-Vorpommern, Schleswig-Holstein and Brandenburg lie within 100 km of Rostock?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_OPERATION.txt](prompts/extract_SPATIAL_OPERATION.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 5 | SQL · SPATIAL_OPERATION → buffer_within | [sql_SPATIAL_OPERATION_buffer_within.txt](prompts/sql_SPATIAL_OPERATION_buffer_within.txt) |

### 1 · Classify

**Model sees**

```text
Which of Mecklenburg-Vorpommern, Schleswig-Holstein and Brandenburg lie within 100 km of Rostock?
```

**Model must answer**

```json
{"query_type": "SPATIAL_OPERATION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which of Mecklenburg-Vorpommern, Schleswig-Holstein and Brandenburg lie within 100 km of Rostock?
```

**Model must answer**

```json
{
  "operation": "BufferWithin",
  "spatial": ["Rostock", "Mecklenburg-Vorpommern", "Schleswig-Holstein", "Brandenburg"],
  "entity_type": "state",
  "distance_km": 100
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Rostock']",
  "entity_type": "city",
  "spatial": ["Rostock"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Brandenburg', 'Mecklenburg-Vorpommern', 'Schleswig-Holstein']",
  "entity_type": "state",
  "spatial": ["Brandenburg", "Mecklenburg-Vorpommern", "Schleswig-Holstein"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 5 · SQL · SPATIAL_OPERATION → buffer_within

**Model sees**

```json
{
  "question": "Which of Mecklenburg-Vorpommern, Schleswig-Holstein and Brandenburg lie within 100 km of Rostock?",
  "operation": "BufferWithin",
  "spatial": ["Rostock", "Mecklenburg-Vorpommern", "Schleswig-Holstein", "Brandenburg"],
  "distance_km": 100.0
}
```

**Model must answer**

```sql
WITH targets(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), zone(g) AS (SELECT ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) SELECT targets.entity_name AS entity_name, CASE WHEN targets.shape IS NULL THEN -1 WHEN ST_Intersects(targets.shape, zone.g) THEN 1 ELSE 0 END AS meets_zone FROM targets, zone
```

---

# relationship

## r01 · SPATIAL_ADJACENCY

> Which states border Hessen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states border Hessen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states border Hessen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": null, "refs": ["Hessen"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen', 'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen', 'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen', 'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen']",
  "entity_type": "state",
  "spatial": ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Hessen?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Hessen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r02 · SPATIAL_ADJACENCY

> Does Brandenburg share a border with Sachsen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Does Brandenburg share a border with Sachsen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Does Brandenburg share a border with Sachsen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": "Brandenburg", "refs": ["Sachsen"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Brandenburg', 'Sachsen']",
  "entity_type": "state",
  "spatial": ["Brandenburg", "Sachsen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Sachsen?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Sachsen"], "subject": "Brandenburg", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r03 · SPATIAL_ADJACENCY

> Is Saarland adjacent to Rheinland-Pfalz?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Is Saarland adjacent to Rheinland-Pfalz?
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Is Saarland adjacent to Rheinland-Pfalz?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": "Saarland", "refs": ["Rheinland-Pfalz"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Rheinland-Pfalz?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Rheinland-Pfalz"], "subject": "Saarland", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r04 · SPATIAL_ADJACENCY

> Name the neighbours of Niedersachsen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Name the neighbours of Niedersachsen
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Name the neighbours of Niedersachsen
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": null, "refs": ["Niedersachsen"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Niedersachsen?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Niedersachsen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r05 · SPATIAL_ADJACENCY

> Which state touches both Bayern and Thüringen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which state touches both Bayern and Thüringen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Which state touches both Bayern and Thüringen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": null, "refs": ["Bayern", "Thüringen"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Bayern, Thüringen?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Bayern", "Thüringen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r06 · SPATIAL_ADJACENCY

> Do Hamburg and Bremen touch?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Do Hamburg and Bremen touch?
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Do Hamburg and Bremen touch?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "adjacency", "subject": "Hamburg", "refs": ["Bremen"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Bremen', 'Hamburg']",
  "entity_type": "state",
  "spatial": ["Bremen", "Hamburg"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states border Bremen?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Bremen"], "subject": "Hamburg", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r07 · SPATIAL_ADJACENCY

> Which states share a border with Baden-Württemberg? Show their population in 2021.

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states share a border with Baden-Württemberg? Show their population in 2021.
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states share a border with Baden-Württemberg? Show their population in 2021.
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2021],
  "attributes": ["population"],
  "spatial_relationship": {"type": "adjacency", "subject": null, "refs": ["Baden-Württemberg"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

*the data fetch for the resulting states follows; it is the DIRECT_LOOKUP fetch pattern and depends on the map, so not generated here*

**Model sees**

```json
{
  "question": "Which of the candidate states border Baden-Württemberg?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Baden-Württemberg"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r08 · SPATIAL_ADJACENCY

> Neighbouring states of Mecklenburg-Vorpommern and their marriages from 2019 to 2020

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_ADJACENCY.txt](prompts/extract_SPATIAL_ADJACENCY.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Neighbouring states of Mecklenburg-Vorpommern and their marriages from 2019 to 2020
```

**Model must answer**

```json
{"query_type": "SPATIAL_ADJACENCY"}
```

### 2 · Extract

**Model sees**

```text
Query: Neighbouring states of Mecklenburg-Vorpommern and their marriages from 2019 to 2020
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2019, 2020],
  "attributes": ["marriages"],
  "spatial_relationship": {"type": "adjacency", "subject": null, "refs": ["Mecklenburg-Vorpommern"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

*the data fetch for the resulting states follows; it is the DIRECT_LOOKUP fetch pattern and depends on the map, so not generated here*

**Model sees**

```json
{
  "question": "Which of the candidate states border Mecklenburg-Vorpommern?",
  "spatial_relationship": {"type": "adjacency", "refs": ["Mecklenburg-Vorpommern"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_Intersects(cand.shape, ref.shape) AND NOT ST_Equals(cand.shape, ref.shape)
```

---

## r09 · SPATIAL_DIRECTION

> Which states lie south of Niedersachsen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states lie south of Niedersachsen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states lie south of Niedersachsen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "south_of", "subject": null, "refs": ["Niedersachsen"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie south of Niedersachsen?",
  "spatial_relationship": {"type": "south_of", "refs": ["Niedersachsen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 135 AND bearing.az <= 225 ORDER BY bearing.az
```

---

## r10 · SPATIAL_DIRECTION · validation

> Is Hamburg north of Hessen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Is Hamburg north of Hessen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Is Hamburg north of Hessen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "north_of", "subject": "Hamburg", "refs": ["Hessen"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hamburg', 'Hessen']",
  "entity_type": "state",
  "spatial": ["Hamburg", "Hessen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie north of Hessen?",
  "spatial_relationship": {"type": "north_of", "refs": ["Hessen"], "subject": "Hamburg", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE (bearing.az >= 315 OR bearing.az <= 45) ORDER BY bearing.az
```

---

## r11 · SPATIAL_DIRECTION

> States east of Nordrhein-Westfalen

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
States east of Nordrhein-Westfalen
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: States east of Nordrhein-Westfalen
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "east_of", "subject": null, "refs": ["Nordrhein-Westfalen"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie east of Nordrhein-Westfalen?",
  "spatial_relationship": {"type": "east_of", "refs": ["Nordrhein-Westfalen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 45 AND bearing.az <= 135 ORDER BY bearing.az
```

---

## r12 · SPATIAL_DIRECTION

> Does Saarland lie west of Bayern?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Does Saarland lie west of Bayern?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Does Saarland lie west of Bayern?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "west_of", "subject": "Saarland", "refs": ["Bayern"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Bayern', 'Saarland']",
  "entity_type": "state",
  "spatial": ["Bayern", "Saarland"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie west of Bayern?",
  "spatial_relationship": {"type": "west_of", "refs": ["Bayern"], "subject": "Saarland", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 225 AND bearing.az <= 315 ORDER BY bearing.az
```

---

## r13 · SPATIAL_DIRECTION

> Which federal states are located north of Thüringen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which federal states are located north of Thüringen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which federal states are located north of Thüringen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "north_of", "subject": null, "refs": ["Thüringen"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie north of Thüringen?",
  "spatial_relationship": {"type": "north_of", "refs": ["Thüringen"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE (bearing.az >= 315 OR bearing.az <= 45) ORDER BY bearing.az
```

---

## r14 · SPATIAL_DIRECTION

> Is Sachsen east of Hessen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Is Sachsen east of Hessen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Is Sachsen east of Hessen?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "east_of", "subject": "Sachsen", "refs": ["Hessen"], "distance_km": null}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Hessen', 'Sachsen']",
  "entity_type": "state",
  "spatial": ["Hessen", "Sachsen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie east of Hessen?",
  "spatial_relationship": {"type": "east_of", "refs": ["Hessen"], "subject": "Sachsen", "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 45 AND bearing.az <= 135 ORDER BY bearing.az
```

---

## r15 · SPATIAL_DIRECTION

> States west of Sachsen-Anhalt with their live births in 2022

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
States west of Sachsen-Anhalt with their live births in 2022
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: States west of Sachsen-Anhalt with their live births in 2022
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2022],
  "attributes": ["live_births"],
  "spatial_relationship": {"type": "west_of", "subject": null, "refs": ["Sachsen-Anhalt"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

*the data fetch for the resulting states follows; it is the DIRECT_LOOKUP fetch pattern and depends on the map, so not generated here*

**Model sees**

```json
{
  "question": "Which of the candidate states lie west of Sachsen-Anhalt?",
  "spatial_relationship": {"type": "west_of", "refs": ["Sachsen-Anhalt"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 225 AND bearing.az <= 315 ORDER BY bearing.az
```

---

## r16 · SPATIAL_DIRECTION

> Which states are south of Brandenburg?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DIRECTION.txt](prompts/extract_SPATIAL_DIRECTION.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states are south of Brandenburg?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DIRECTION"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states are south of Brandenburg?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "south_of", "subject": null, "refs": ["Brandenburg"], "distance_km": null}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie south of Brandenburg?",
  "spatial_relationship": {"type": "south_of", "refs": ["Brandenburg"], "subject": null, "distance_km": null}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)), bearing(entity_name, az) AS (SELECT cand.entity_name, degrees(ST_Azimuth(ST_Centroid(ref.shape), ST_Centroid(cand.shape))) FROM cand, ref WHERE cand.entity_name <> :ref) SELECT bearing.entity_name AS entity_name FROM bearing WHERE bearing.az >= 135 AND bearing.az <= 225 ORDER BY bearing.az
```

---

## r17 · SPATIAL_DISTANCE

> Which states are within 150 km of Frankfurt?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states are within 150 km of Frankfurt?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states are within 150 km of Frankfurt?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "distance", "subject": null, "refs": ["Frankfurt"], "distance_km": 150}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 150 km of Frankfurt?",
  "spatial_relationship": {"type": "distance", "refs": ["Frankfurt"], "subject": null, "distance_km": 150}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

## r18 · SPATIAL_DISTANCE

> Is Thüringen within 50 km of Leipzig?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Is Thüringen within 50 km of Leipzig?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: Is Thüringen within 50 km of Leipzig?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "distance", "subject": "Thüringen", "refs": ["Leipzig"], "distance_km": 50}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 50 km of Leipzig?",
  "spatial_relationship": {"type": "distance", "refs": ["Leipzig"], "subject": "Thüringen", "distance_km": 50}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

## r19 · SPATIAL_DISTANCE

> States within 200 km of Berlin

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
States within 200 km of Berlin
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: States within 200 km of Berlin
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "distance", "subject": null, "refs": ["Berlin"], "distance_km": 200}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 200 km of Berlin?",
  "spatial_relationship": {"type": "distance", "refs": ["Berlin"], "subject": null, "distance_km": 200}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

## r20 · SPATIAL_DISTANCE · validation

> Which states lie within 80 km of Stuttgart?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Which states lie within 80 km of Stuttgart?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: Which states lie within 80 km of Stuttgart?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "distance", "subject": null, "refs": ["Stuttgart"], "distance_km": 80}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 80 km of Stuttgart?",
  "spatial_relationship": {"type": "distance", "refs": ["Stuttgart"], "subject": null, "distance_km": 80}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

## r21 · SPATIAL_DISTANCE

> Is Bremen within 100 km of Hannover?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · shape fetch (state) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
Is Bremen within 100 km of Hannover?
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: Is Bremen within 100 km of Hannover?
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [],
  "attributes": [],
  "spatial_relationship": {"type": "distance", "subject": "Bremen", "refs": ["Hannover"], "distance_km": 100}
}
```

### 3 · SQL · shape fetch (state)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these state names: ['Bremen']",
  "entity_type": "state",
  "spatial": ["Bremen"]
}
```

**Model must answer**

```sql
SELECT s.state_name AS entity_name, ST_AsText(s.geo_shape) AS wkt, ST_SRID(s.geo_shape) AS srid FROM states s WHERE s.state_name = ANY(:names)
```

### 4 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Hannover']",
  "entity_type": "city",
  "spatial": ["Hannover"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 5 · SQL · SPATIAL_RELATIONSHIP → compute

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 100 km of Hannover?",
  "spatial_relationship": {"type": "distance", "refs": ["Hannover"], "subject": "Bremen", "distance_km": 100}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

## r22 · SPATIAL_DISTANCE

> States within 120 km of Köln and their population in 2020

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_DISTANCE.txt](prompts/extract_SPATIAL_DISTANCE.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP → compute | [sql_SPATIAL_RELATIONSHIP_compute.txt](prompts/sql_SPATIAL_RELATIONSHIP_compute.txt) |

### 1 · Classify

**Model sees**

```text
States within 120 km of Cologne and their population in 2020
```

**Model must answer**

```json
{"query_type": "SPATIAL_DISTANCE"}
```

### 2 · Extract

**Model sees**

```text
Query: States within 120 km of Cologne and their population in 2020
```

**Model must answer**

```json
{
  "spatial": "all",
  "temporal": [2020],
  "attributes": ["population"],
  "spatial_relationship": {"type": "distance", "subject": null, "refs": ["Cologne"], "distance_km": 120}
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP → compute

*the data fetch for the resulting states follows; it is the DIRECT_LOOKUP fetch pattern and depends on the map, so not generated here*

**Model sees**

```json
{
  "question": "Which of the candidate states lie within 120 km of Cologne?",
  "spatial_relationship": {"type": "distance", "refs": ["Cologne"], "subject": null, "distance_km": 120}
}
```

**Model must answer**

```sql
WITH cand(entity_name, shape) AS (SELECT n, ST_GeomFromText(w, 4326) FROM unnest(CAST(:names AS text[]), CAST(:wkts AS text[])) AS t(n, w)), ref(shape) AS (SELECT ST_GeomFromText(:ref_wkt, :ref_srid)) SELECT cand.entity_name AS entity_name FROM cand, ref WHERE cand.entity_name <> :ref AND ST_DWithin(cand.shape::geography, ref.shape::geography, :dist_m) ORDER BY ST_Distance(cand.shape::geography, ref.shape::geography)
```

---

# delegation

## b01 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities are within 30 km of Leipzig?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 5 | SQL · within (answering Agent-1) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 6 | SQL · within (answering Agent-2) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities are within 30 km of Leipzig?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities are within 30 km of Leipzig?
```

**Model must answer**

```json
{
  "spatial": ["Leipzig"],
  "operations": ["Buffer", "Within"],
  "distance_km": 30,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities are within 30 km of Leipzig?",
  "spatial": ["Leipzig"],
  "distance_km": 30.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities are within 30 km of Leipzig?",
  "target_entity": "city",
  "exclude": ["Leipzig"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 5 · SQL · within (answering Agent-1)

*this agent testing its own cities for Agent-1's delegated zone*

**Model sees**

```json
{
  "question": "Agent-1 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Leipzig"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 6 · SQL · within (answering Agent-2)

*this agent testing its own cities for Agent-2's delegated zone*

**Model sees**

```json
{
  "question": "Agent-2 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Leipzig"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b02 · SPATIAL_RELATIONSHIP_BUFFER

> List all cities within 100 km of Frankfurt

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
List all cities within 100 km of Frankfurt
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: List all cities within 100 km of Frankfurt
```

**Model must answer**

```json
{
  "spatial": ["Frankfurt"],
  "operations": ["Buffer", "Within"],
  "distance_km": 100,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "List all cities within 100 km of Frankfurt",
  "spatial": ["Frankfurt"],
  "distance_km": 100.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "List all cities within 100 km of Frankfurt",
  "target_entity": "city",
  "exclude": ["Frankfurt"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b03 · SPATIAL_RELATIONSHIP_BUFFER

> What cities are near Hannover, within 75 km?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
What cities are near Hannover, within 75 km?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: What cities are near Hannover, within 75 km?
```

**Model must answer**

```json
{
  "spatial": ["Hannover"],
  "operations": ["Buffer", "Within"],
  "distance_km": 75,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "What cities are near Hannover, within 75 km?",
  "spatial": ["Hannover"],
  "distance_km": 75.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "What cities are near Hannover, within 75 km?",
  "target_entity": "city",
  "exclude": ["Hannover"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b04 · SPATIAL_RELATIONSHIP_BUFFER

> Cities within 40 km of Köln

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Cities within 40 km of Cologne
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Cities within 40 km of Cologne
```

**Model must answer**

```json
{
  "spatial": ["Cologne"],
  "operations": ["Buffer", "Within"],
  "distance_km": 40,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Cities within 40 km of Köln",
  "spatial": ["Cologne"],
  "distance_km": 40.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Cities within 40 km of Köln",
  "target_entity": "city",
  "exclude": ["Cologne"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b05 · SPATIAL_RELATIONSHIP_BUFFER

> Which towns lie within 60 km of Dresden?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 6 | SQL · within (answering Agent-1) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 7 | SQL · within (answering Agent-2) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which towns lie within 60 km of Dresden?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which towns lie within 60 km of Dresden?
```

**Model must answer**

```json
{
  "spatial": ["Dresden"],
  "operations": ["Buffer", "Within"],
  "distance_km": 60,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Dresden']",
  "entity_type": "city",
  "spatial": ["Dresden"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which towns lie within 60 km of Dresden?",
  "spatial": ["Dresden"],
  "distance_km": 60.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which towns lie within 60 km of Dresden?",
  "target_entity": "city",
  "exclude": ["Dresden"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 6 · SQL · within (answering Agent-1)

*this agent testing its own cities for Agent-1's delegated zone*

**Model sees**

```json
{
  "question": "Agent-1 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Dresden"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 7 · SQL · within (answering Agent-2)

*this agent testing its own cities for Agent-2's delegated zone*

**Model sees**

```json
{
  "question": "Agent-2 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Dresden"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b06 · SPATIAL_RELATIONSHIP_BUFFER

> Find every city in a 120 km radius around Berlin

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Find every city in a 120 km radius around Berlin
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Find every city in a 120 km radius around Berlin
```

**Model must answer**

```json
{
  "spatial": ["Berlin"],
  "operations": ["Buffer", "Within"],
  "distance_km": 120,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Berlin']",
  "entity_type": "city",
  "spatial": ["Berlin"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Find every city in a 120 km radius around Berlin",
  "spatial": ["Berlin"],
  "distance_km": 120.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Find every city in a 120 km radius around Berlin",
  "target_entity": "city",
  "exclude": ["Berlin"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b07 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities are within 25 km of Düsseldorf?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities are within 25 km of Düsseldorf?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities are within 25 km of Düsseldorf?
```

**Model must answer**

```json
{
  "spatial": ["Düsseldorf"],
  "operations": ["Buffer", "Within"],
  "distance_km": 25,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Düsseldorf']",
  "entity_type": "city",
  "spatial": ["Düsseldorf"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities are within 25 km of Düsseldorf?",
  "spatial": ["Düsseldorf"],
  "distance_km": 25.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities are within 25 km of Düsseldorf?",
  "target_entity": "city",
  "exclude": ["Düsseldorf"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b08 · SPATIAL_RELATIONSHIP_BUFFER

> Show the cities close to Stuttgart

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Show the cities close to Stuttgart
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Show the cities close to Stuttgart
```

**Model must answer**

```json
{
  "spatial": ["Stuttgart"],
  "operations": ["Buffer", "Within"],
  "distance_km": 100,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Show the cities close to Stuttgart",
  "spatial": ["Stuttgart"],
  "distance_km": 100.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Show the cities close to Stuttgart",
  "target_entity": "city",
  "exclude": ["Stuttgart"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b09 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities can be found within 200 km of Hamburg?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities can be found within 200 km of Hamburg?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities can be found within 200 km of Hamburg?
```

**Model must answer**

```json
{
  "spatial": ["Hamburg"],
  "operations": ["Buffer", "Within"],
  "distance_km": 200,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities can be found within 200 km of Hamburg?",
  "spatial": ["Hamburg"],
  "distance_km": 200.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities can be found within 200 km of Hamburg?",
  "target_entity": "city",
  "exclude": ["Hamburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b10 · SPATIAL_RELATIONSHIP_BUFFER · validation

> Cities in a 90 km radius of Nürnberg

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 6 | SQL · within (answering Agent-1) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |
| 7 | SQL · within (answering Agent-2) | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Cities in a 90 km radius of Nuremberg
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Cities in a 90 km radius of Nuremberg
```

**Model must answer**

```json
{
  "spatial": ["Nuremberg"],
  "operations": ["Buffer", "Within"],
  "distance_km": 90,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Nuremberg']",
  "entity_type": "city",
  "spatial": ["Nuremberg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Cities in a 90 km radius of Nürnberg",
  "spatial": ["Nuremberg"],
  "distance_km": 90.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Cities in a 90 km radius of Nürnberg",
  "target_entity": "city",
  "exclude": ["Nuremberg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 6 · SQL · within (answering Agent-1)

*this agent testing its own cities for Agent-1's delegated zone*

**Model sees**

```json
{
  "question": "Agent-1 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Nuremberg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

### 7 · SQL · within (answering Agent-2)

*this agent testing its own cities for Agent-2's delegated zone*

**Model sees**

```json
{
  "question": "Agent-2 asks which of our cities lie inside this zone",
  "target_entity": "city",
  "exclude": ["Nuremberg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b11 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities are less than 70 km from Kassel?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities are less than 70 km from Kassel?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities are less than 70 km from Kassel?
```

**Model must answer**

```json
{
  "spatial": ["Kassel"],
  "operations": ["Buffer", "Within"],
  "distance_km": 70,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities are less than 70 km from Kassel?",
  "spatial": ["Kassel"],
  "distance_km": 70.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities are less than 70 km from Kassel?",
  "target_entity": "city",
  "exclude": ["Kassel"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b12 · SPATIAL_RELATIONSHIP_BUFFER

> Name the cities within 150 km of München

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Name the cities within 150 km of Munich
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Name the cities within 150 km of Munich
```

**Model must answer**

```json
{
  "spatial": ["Munich"],
  "operations": ["Buffer", "Within"],
  "distance_km": 150,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Munich']",
  "entity_type": "city",
  "spatial": ["Munich"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Name the cities within 150 km of München",
  "spatial": ["Munich"],
  "distance_km": 150.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Name the cities within 150 km of München",
  "target_entity": "city",
  "exclude": ["Munich"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b13 · SPATIAL_RELATIONSHIP_BUFFER

> Are there any cities within 35 km of Bremen?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Are there any cities within 35 km of Bremen?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Are there any cities within 35 km of Bremen?
```

**Model must answer**

```json
{
  "spatial": ["Bremen"],
  "operations": ["Buffer", "Within"],
  "distance_km": 35,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Bremen']",
  "entity_type": "city",
  "spatial": ["Bremen"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Are there any cities within 35 km of Bremen?",
  "spatial": ["Bremen"],
  "distance_km": 35.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Are there any cities within 35 km of Bremen?",
  "target_entity": "city",
  "exclude": ["Bremen"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b14 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities lie within 80 km of Erfurt?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities lie within 80 km of Erfurt?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities lie within 80 km of Erfurt?
```

**Model must answer**

```json
{
  "spatial": ["Erfurt"],
  "operations": ["Buffer", "Within"],
  "distance_km": 80,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Erfurt']",
  "entity_type": "city",
  "spatial": ["Erfurt"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities lie within 80 km of Erfurt?",
  "spatial": ["Erfurt"],
  "distance_km": 80.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities lie within 80 km of Erfurt?",
  "target_entity": "city",
  "exclude": ["Erfurt"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b15 · SPATIAL_RELATIONSHIP_BUFFER

> cities within 45km of Mainz

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
cities within 45km of Mainz
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: cities within 45km of Mainz
```

**Model must answer**

```json
{
  "spatial": ["Mainz"],
  "operations": ["Buffer", "Within"],
  "distance_km": 45,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Mainz']",
  "entity_type": "city",
  "spatial": ["Mainz"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "cities within 45km of Mainz",
  "spatial": ["Mainz"],
  "distance_km": 45.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "cities within 45km of Mainz",
  "target_entity": "city",
  "exclude": ["Mainz"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b16 · SPATIAL_RELATIONSHIP_BUFFER

> What cities are located within 100 kilometres of Kiel?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
What cities are located within 100 kilometres of Kiel?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: What cities are located within 100 kilometres of Kiel?
```

**Model must answer**

```json
{
  "spatial": ["Kiel"],
  "operations": ["Buffer", "Within"],
  "distance_km": 100,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Kiel']",
  "entity_type": "city",
  "spatial": ["Kiel"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "What cities are located within 100 kilometres of Kiel?",
  "spatial": ["Kiel"],
  "distance_km": 100.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "What cities are located within 100 kilometres of Kiel?",
  "target_entity": "city",
  "exclude": ["Kiel"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b17 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities are within 55 km of Magdeburg?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities are within 55 km of Magdeburg?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities are within 55 km of Magdeburg?
```

**Model must answer**

```json
{
  "spatial": ["Magdeburg"],
  "operations": ["Buffer", "Within"],
  "distance_km": 55,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Magdeburg']",
  "entity_type": "city",
  "spatial": ["Magdeburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities are within 55 km of Magdeburg?",
  "spatial": ["Magdeburg"],
  "distance_km": 55.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities are within 55 km of Magdeburg?",
  "target_entity": "city",
  "exclude": ["Magdeburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b18 · SPATIAL_RELATIONSHIP_BUFFER

> Give me all cities within 65 km of Rostock

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Give me all cities within 65 km of Rostock
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Give me all cities within 65 km of Rostock
```

**Model must answer**

```json
{
  "spatial": ["Rostock"],
  "operations": ["Buffer", "Within"],
  "distance_km": 65,
  "target_entity": "city"
}
```

### 3 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Give me all cities within 65 km of Rostock",
  "spatial": ["Rostock"],
  "distance_km": 65.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Give me all cities within 65 km of Rostock",
  "target_entity": "city",
  "exclude": ["Rostock"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b19 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities lie within 110 km of Freiburg?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities lie within 110 km of Freiburg?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities lie within 110 km of Freiburg?
```

**Model must answer**

```json
{
  "spatial": ["Freiburg"],
  "operations": ["Buffer", "Within"],
  "distance_km": 110,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Freiburg']",
  "entity_type": "city",
  "spatial": ["Freiburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities lie within 110 km of Freiburg?",
  "spatial": ["Freiburg"],
  "distance_km": 110.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities lie within 110 km of Freiburg?",
  "target_entity": "city",
  "exclude": ["Freiburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b20 · SPATIAL_RELATIONSHIP_BUFFER · validation

> Cities that are at most 50 km away from Bonn

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Cities that are at most 50 km away from Bonn
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Cities that are at most 50 km away from Bonn
```

**Model must answer**

```json
{
  "spatial": ["Bonn"],
  "operations": ["Buffer", "Within"],
  "distance_km": 50,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Bonn']",
  "entity_type": "city",
  "spatial": ["Bonn"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Cities that are at most 50 km away from Bonn",
  "spatial": ["Bonn"],
  "distance_km": 50.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Cities that are at most 50 km away from Bonn",
  "target_entity": "city",
  "exclude": ["Bonn"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b21 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities surround Augsburg within 40 km?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities surround Augsburg within 40 km?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities surround Augsburg within 40 km?
```

**Model must answer**

```json
{
  "spatial": ["Augsburg"],
  "operations": ["Buffer", "Within"],
  "distance_km": 40,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Augsburg']",
  "entity_type": "city",
  "spatial": ["Augsburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities surround Augsburg within 40 km?",
  "spatial": ["Augsburg"],
  "distance_km": 40.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities surround Augsburg within 40 km?",
  "target_entity": "city",
  "exclude": ["Augsburg"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

## b22 · SPATIAL_RELATIONSHIP_BUFFER

> Which cities are within 85 km of Münster?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |
| 2 | Extract | [extract_SPATIAL_RELATIONSHIP_BUFFER.txt](prompts/extract_SPATIAL_RELATIONSHIP_BUFFER.txt) |
| 3 | SQL · shape fetch (city) | [sql_GEOMETRY_LOOKUP_fetch.txt](prompts/sql_GEOMETRY_LOOKUP_fetch.txt) |
| 4 | SQL · SPATIAL_RELATIONSHIP_BUFFER → zone | [sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_zone.txt) |
| 5 | SQL · SPATIAL_RELATIONSHIP_BUFFER → within | [sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt](prompts/sql_SPATIAL_RELATIONSHIP_BUFFER_within.txt) |

### 1 · Classify

**Model sees**

```text
Which cities are within 85 km of Münster?
```

**Model must answer**

```json
{"query_type": "SPATIAL_RELATIONSHIP_BUFFER"}
```

### 2 · Extract

**Model sees**

```text
Query: Which cities are within 85 km of Münster?
```

**Model must answer**

```json
{
  "spatial": ["Münster"],
  "operations": ["Buffer", "Within"],
  "distance_km": 85,
  "target_entity": "city"
}
```

### 3 · SQL · shape fetch (city)

**Model sees**

```json
{
  "question": "Fetch the stored shapes of these city names: ['Münster']",
  "entity_type": "city",
  "spatial": ["Münster"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.city_name = ANY(:names)
```

### 4 · SQL · SPATIAL_RELATIONSHIP_BUFFER → zone

**Model sees**

```json
{
  "question": "Which cities are within 85 km of Münster?",
  "spatial": ["Münster"],
  "distance_km": 85.0
}
```

**Model must answer**

```sql
SELECT ST_AsText(ST_Buffer(ST_GeomFromText(:ref_wkt, :ref_srid)::geography, :dist_m)::geometry) AS wkt, :ref_srid AS srid
```

### 5 · SQL · SPATIAL_RELATIONSHIP_BUFFER → within

**Model sees**

```json
{
  "question": "Which cities are within 85 km of Münster?",
  "target_entity": "city",
  "exclude": ["Münster"]
}
```

**Model must answer**

```sql
SELECT c.city_name AS entity_name, ST_AsText(c.centroid) AS wkt, ST_SRID(c.centroid) AS srid FROM cities c WHERE c.centroid IS NOT NULL AND ST_Within(c.centroid, ST_GeomFromText(:zone_wkt, :zone_srid)) AND NOT (c.city_name = ANY(:exclude))
```

---

# unrelated

## u01 · UNRELATED

> What is the capital of Italy?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
What is the capital of Italy?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u02 · UNRELATED

> How do I cook pasta?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
How do I cook pasta?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u03 · UNRELATED

> What was the population of Vienna in 2021?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
What was the population of Vienna in 2021?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u04 · UNRELATED

> Translate 'good morning' into Spanish

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
Translate 'good morning' into Spanish
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u05 · UNRELATED

> Who is the current chancellor of Germany?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
Who is the current chancellor of Germany?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u06 · UNRELATED

> Show me the weather forecast for tomorrow

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
Show me the weather forecast for tomorrow
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u07 · UNRELATED

> How many people live in London?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
How many people live in London?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u08 · UNRELATED

> Write a short poem about rivers

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
Write a short poem about rivers
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u09 · UNRELATED

> What is 25 times 4?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
What is 25 times 4?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---

## u10 · UNRELATED · validation

> Which Swiss cantons border France?

| # | Call | System prompt |
|---|---|---|
| 1 | Classify | [classify.txt](prompts/classify.txt) |

### 1 · Classify

**Model sees**

```text
Which Swiss cantons border France?
```

**Model must answer**

```json
{"query_type": "UNRELATED"}
```

---
