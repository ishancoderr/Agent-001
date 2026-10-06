# How to write the questions file

`questions_vN.yaml` is the only file in this folder a person writes. Each entry is one question a user might ask the agent, its category, and the extraction the agent **should** produce for it. Everything else — prompts, SQL, train/validation files — is generated from it by `build_examples.py`.

**Who writes it:** the thesis author. Version 1 (120 questions) was drafted with Claude Code following the plan in this guide; every question and label should be reviewed by the author before results are reported.

---

## 1. One entry

```yaml
- {id: d10, category: DIRECT_LOOKUP,
   question: "How many residents did Brandenburg have in 2020?",
   extract: {spatial: [Brandenburg], temporal: [2020], attributes: [population], entity_type: state}}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique. Group prefix + number: `d` data, `g` geometry, `o` operation, `r` relationship, `b` delegation, `u` unrelated |
| `category` | yes | The correct classify label (section 3) |
| `question` | yes | The question exactly as a user would type it — typos and odd spelling welcome |
| `extract` | yes, except UNRELATED | The correct extraction, in the format of that category (section 3) |
| `presence: [..]` | no | DIRECT_LOOKUP only: assume the fetch found **no rows** for these places, so the presence step is trained too |
| `peer: true` | no | DIRECT_LOOKUP / delegation: also train the SQL this agent runs when the **other agent** asks for this |
| `expect: NEEDS_YEAR` | no | DIRECT_LOOKUP with no year: the parser must turn it into NEEDS_YEAR (no SQL is generated) |
| `names_translated: true` | no | The label spells a name differently from the question (Bavaria → Bayern); turns off the "name is in the question" check |

---

## 2. Names: label what the model actually sees

Before the model sees a question, the agent's `CleanQuery` rewrites some place names. **The extraction must use the names as they look after cleaning.**

| The user writes | The model sees | Label it as |
|---|---|---|
| Thueringen, Baden-Wuerttemberg | Thüringen, Baden-Württemberg | Thüringen, Baden-Württemberg |
| nordrhein westfalen, Mecklenburg Vorpommern | Nordrhein-Westfalen, Mecklenburg-Vorpommern | the hyphenated form |
| München / Muenchen / Munich | **Munich** | Munich |
| Köln / Koeln | **Cologne** | Cologne |
| Nürnberg / Nuernberg | **Nuremberg** | Nuremberg |
| Bavaria, Hesse, Lower Saxony, Saxony, NRW | *unchanged* | the German name (Bayern, Hessen, Niedersachsen, Sachsen, Nordrhein-Westfalen) **+ `names_translated: true`** |
| Frankfurt, Leipzig, Dresden, … | *unchanged* | as written |

Not sure what the model will see? Ask the agent (from `Agent-001/`):

```bash
python -c "from agent1.pipeline.clean_query import CleanQuery; print(CleanQuery('geometry of Muenchen').cleaned)"
```

The sixteen states, spelled as stored: Baden-Württemberg, Bayern, Berlin, Brandenburg, Bremen, Hamburg, Hessen, Mecklenburg-Vorpommern, Niedersachsen, Nordrhein-Westfalen, Rheinland-Pfalz, Saarland, Sachsen, Sachsen-Anhalt, Schleswig-Holstein, Thüringen.

---

## 3. The format per category

### DIRECT_LOOKUP — stored values (group `d`)

```yaml
- {id: d03, category: DIRECT_LOOKUP,
   question: "Show me the number of marriages in Niedersachsen from 2018 to 2021.",
   extract: {spatial: [Niedersachsen], temporal: [2018, 2019, 2020, 2021], attributes: [marriages], entity_type: state}}
```

- `spatial`: a list of states, or `all` for "every state".
- `temporal`: **every** year written out — "2018 to 2021" is `[2018, 2019, 2020, 2021]`, never a start/end pair.
- `attributes`: only `population`, `marriages`, `live_births`. The user's words map to them:

  | User says | Attribute |
  |---|---|
  | people, inhabitants, residents, "how many lived" | population |
  | married, marriage, "couples got married" | marriages |
  | births, live birth, "babies were born" | live_births |

- `entity_type`: `state`.
- **No year in the question** → `temporal: []` and `expect: NEEDS_YEAR`.
- Avoid "this year", "now", "currently": they become `CURRENT_YEAR`, which changes every year and would make the label wrong next year.

### GEOMETRY_LOOKUP — stored shapes (group `g`)

```yaml
- {id: g14, category: GEOMETRY_LOOKUP, question: "Give me the shapes of Hessen and Kassel",
   extract: {entities: [{entity_name: Hessen, entity_type: state}, {entity_name: Kassel, entity_type: city}]}}
```

- Every place asked about, in question order, each with `state` or `city`.
- Berlin, Hamburg and Bremen are both: label them `state` unless the question says "the city of …".
- Words that mean this category: geometry, shape, boundary, border (of one place), outline, polygon, WKT, coordinates, point, centroid, location.

### SPATIAL_OPERATION — a new shape from named places (group `o`)

```yaml
- {id: o11, category: SPATIAL_OPERATION, question: "Remove Hamburg from Schleswig-Holstein",
   extract: {operation: Difference, spatial: [Schleswig-Holstein, Hamburg], entity_type: state, distance_km: null}}
```

| operation | Meaning | User says |
|---|---|---|
| `Union` | one combined shape | combine, merge, join, one area for |
| `Intersection` | the shared area | in common, overlap, shared by, intersection |
| `Difference` | the first minus the second | without, minus, remove … from, cut out |
| `SymDifference` | in one but not both | not in both, symmetric difference, exactly one of |
| `BufferWithin` | which **named** places lie within N km of a city | "Which of X and Y lie within N km of Z?" |

- **Difference: the first entry is the shape that is reduced** — even when the question names it second ("Remove Hamburg from Schleswig-Holstein" → `[Schleswig-Holstein, Hamburg]`).
- **BufferWithin:** `spatial[0]` is the reference city, the rest are the named candidates; `distance_km` is the distance (100 if none is given). For the other four, `distance_km: null`.
- `entity_type: state` unless every place is a city.

### SPATIAL_ADJACENCY / SPATIAL_DIRECTION / SPATIAL_DISTANCE — relationships (group `r`)

```yaml
- {id: r02, category: SPATIAL_ADJACENCY, question: "Does Brandenburg share a border with Sachsen?",
   extract: {spatial: all, temporal: [], attributes: [],
             spatial_relationship: {type: adjacency, subject: Brandenburg, refs: [Sachsen], distance_km: null}}}

- {id: r07, category: SPATIAL_ADJACENCY, question: "Which states share a border with Baden-Württemberg? Show their population in 2021.",
   extract: {spatial: all, temporal: [2021], attributes: [population],
             spatial_relationship: {type: adjacency, subject: null, refs: [Baden-Württemberg], distance_km: null}}}
```

| category | `type` | Example question |
|---|---|---|
| SPATIAL_ADJACENCY | `adjacency` | Which states border Hessen? / Do X and Y touch? |
| SPATIAL_DIRECTION | `north_of`, `south_of`, `east_of`, `west_of` | Which states lie south of Niedersachsen? |
| SPATIAL_DISTANCE | `distance` (+ `distance_km`) | Which states are within 150 km of Frankfurt? |

- `spatial` is always `all`.
- **Yes/no question** → `subject` is the place asked about, `refs` what it is measured against ("Is Hamburg north of Hessen?" → subject Hamburg, refs [Hessen]).
- **"Which states …" question** → `subject: null`, every named place in `refs`.
- `temporal: []` and `attributes: []` unless the question also asks for data ("… and their population in 2021").
- `distance_km` only for `distance`; otherwise `null`.

### SPATIAL_RELATIONSHIP_BUFFER — cities that cannot be named (group `b`)

```yaml
- {id: b03, category: SPATIAL_RELATIONSHIP_BUFFER, question: "What cities are near Hannover, within 75 km?",
   extract: {spatial: [Hannover], operations: [Buffer, Within], distance_km: 75, target_entity: city}}
```

- The question asks **which cities** lie within some distance of one city; the answer cities are not named (that is what separates it from BufferWithin).
- `spatial`: the one reference city. `operations` is always `[Buffer, Within]`, `target_entity` always `city`.
- `distance_km`: the distance named, **100 if none** ("cities close to Stuttgart").

### UNRELATED — outside the system (group `u`)

```yaml
- {id: u07, category: UNRELATED, question: "How many people live in London?"}
```

Only `id`, `category` and `question`. Good ones: other countries ("population of Vienna"), small talk, maths, translation, general knowledge — and questions that look similar to real ones but are not about German states or cities.

---

## 4. Writing good questions

**Vary everything except the meaning.** The model should learn the task, not one sentence:

| Vary | For example |
|---|---|
| wording | "How many residents …", "Inhabitants of …", "population 2024", a statement instead of a question |
| words for attributes | people / inhabitants / residents, births / babies were born |
| spelling | missing umlauts, lowercase, missing hyphens, English names |
| places | all sixteen states, many different cities, one place or several |
| years | single years, ranges, two separate years, "all states" |
| distances | small and large, with and without "km" |

**Cover the hard cases on purpose:** reversed order for Difference, Berlin/Hamburg/Bremen as state vs city, yes/no vs "which" relationships, relationships that also ask for data, questions with no year, distances not given.

**Balance the groups.** Version 1 has 22 questions per main group and 10 unrelated. Within a group, spread the sub-types (each operation, each direction, …).

**Never use test questions.** The 20 scenario questions of the thesis and the test set must not appear here, not even reworded closely — otherwise the test measures memory, not ability.

**Avoid questions whose category is a matter of opinion.** "Are Sachsen and Brandenburg within 50 km of Leipzig?" could be SPATIAL_DISTANCE or SPATIAL_OPERATION. Write "Which of Sachsen and Brandenburg lie within 50 km of Leipzig?" (clearly BufferWithin) instead.

---

## 5. Adding questions without disturbing the split

The split counts questions **per group, in file order**: the 10th, 20th, 30th … question of each group goes to validation. So:

- **Add new questions at the end of their group.** Inserting in the middle shifts which existing questions are in validation.
- **Never change or reuse an id** once results have been reported with it.
- For a real change, start a new version: copy `questions_v1.yaml` to `questions_v2.yaml`, keep the old questions, continue the ids (d23, d24, …). Keep v1 as it is — your first results were measured on it.

---

## 6. Check your work

```bash
python -m finetune.build_examples finetune/questions_v1.yaml
python -m finetune.check_dataset  finetune/questions_v1.jsonl
```

The check must end with `failed 0`. Typical messages and what to do:

| Message | Cause | Fix |
|---|---|---|
| `name(s) not in the question text: ['München']` | the label uses the spelling before cleaning | label `Munich` (section 2) — or add `names_translated: true` for an English name |
| `not one of the sixteen states: [...]` | a city or misspelled state in a DIRECT_LOOKUP | fix the spelling; cities have no demographic data |
| `unknown attribute(s) [...]` | not `population` / `marriages` / `live_births` | use the attribute name, not the user's word |
| `parser produced NEEDS_YEAR, expected DIRECT_LOOKUP` | `temporal` is empty | add the years — or add `expect: NEEDS_YEAR` if there really is none |
| `classify says X, extract used Y` | two different categories for one question | entries have one `category`; check for a copy-paste mistake |
| `conflicting answers for the same input` | the same question with two different labels | keep one |
| `system prompt differs from today's prompt` | a prompt in `config/prompts/` changed | run `build_examples` again |

Then open `questions_v1_review.csv` and read the lines the checker lists. The checker proves a label is valid; only you can tell whether it is right.
