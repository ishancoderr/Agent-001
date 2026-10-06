# finetune/ — training data for the fine-tuned model

The agent calls a language model three times per question: **classify** (which category), **extract** (places, years, attributes, …) and **SQL** (one PostGIS statement per retrieval step). This folder produces the data to fine-tune a model on exactly those calls.

Training itself happens in the separate repository [kqml-geo-qwen3-qlora](https://github.com/ishancoderr/kqml-geo-qwen3-qlora) (Colab notebook and script). This folder makes the data, because making it needs the agent's own code: its prompts, name cleaning, parser and SQL validator.

## Files

| File | What it is | Edited by |
|---|---|---|
| [questions_v1.yaml](questions_v1.yaml) | The questions, each with its category and correct extraction | **a person** — see [HOW_TO_WRITE_QUESTIONS.md](HOW_TO_WRITE_QUESTIONS.md) |
| [build_examples.py](build_examples.py) | Turns the YAML into training data: one example per LLM call, train/validation split, duplicates removed | — |
| [check_dataset.py](check_dataset.py) | Checks every example with the agent's own parser and SQL validator; writes a spreadsheet for spot-checks | — |
| [reference_sql.py](reference_sql.py) | Writes the correct SQL for every step from `config/schema/*.yaml` | — |

Generated (not committed — ignored in the repository's root [.gitignore](../.gitignore); rebuild them any time):

| File | What it is |
|---|---|
| `questions_v1_train.jsonl` / `questions_v1_val.jsonl` | the training and validation data |
| `questions_v1.jsonl` | both together, for checking |
| `questions_v1.md` | every example laid out for reading |
| `prompts/*.txt` | each system prompt once |
| `*_review.csv` | the spot-check spreadsheet from `check_dataset.py` |

## Workflow

```
 1. WRITE    questions_v1.yaml                       question + category + correct extraction
                   │
 2. BUILD    python -m finetune.build_examples       → train / val JSONL, .md, prompts/
                   │
 3. CHECK    python -m finetune.check_dataset        → must end with "failed 0"
                   │
 4. REVIEW   read the 10 lines it lists in questions_v1_review.csv
                   │
 5. PUBLISH  copy to kqml-geo-qwen3-qlora/data/, commit, push → train in Colab
```

Run the commands from the **repository root** (`Agent-001/`), in the same Python environment as the agent:

```bash
python -m finetune.build_examples                                  # questions_v1.yaml by default
python -m finetune.check_dataset                                   # questions_v1.jsonl by default

python -m finetune.build_examples finetune/questions_v2.yaml       # another version
python -m finetune.check_dataset  finetune/questions_v2.jsonl
```

Step 5 copies these files into `kqml-geo-qwen3-qlora/data/`: `questions_vN.yaml`, `questions_vN_train.jsonl`, `questions_vN_val.jsonl`, `questions_vN.md` and `prompts/`.

## What `build_examples.py` does with one question

```
d05 "Give me population, marriages and live births for Rheinland-Pfalz in 2023."   (peer: true)
 ├─ classify                           → {"query_type": "DIRECT_LOOKUP"}
 ├─ extract                            → {"spatial": ["Rheinland-Pfalz"], "temporal": [2023], ...}
 ├─ sql fetch                          → SELECT s.state_name AS entity_name, sd.stat_year AS year, ...
 ├─ sql fetch, "Agent-1 asks for ..."  → the same SQL, when the OTHER agent asks
 └─ sql fetch, "Agent-2 asks for ..."  → (both wordings: one model serves both agents)
```

Everything except the question and the extraction is derived the way the agent does it at run time:

| Part of the example | Comes from |
|---|---|
| question text the model sees | `CleanQuery` (Thueringen → Thüringen, München → Munich) |
| system prompts | the agent's prompt loader and `SqlWriter._system_prompt()` |
| input of each SQL step | the same parameters `gap_detector.py` / `spatial_compute.py` pass |
| correct SQL | `reference_sql.py`, from the schema YAMLs; must pass `validate_sql()` |

## Train / validation split

- **By question, not by example** — all examples of a question go to the same file, so the model is never tested on half of a question it was trained on.
- **Every 10th question of each group goes to validation** (d10, d20, g10, …), so every category is represented there.
- **Duplicates are removed with training first** — an example identical to a training example is dropped from validation (every "which states …" question fetches the same sixteen shapes).

Version 1: 120 questions → 413 examples → **375 train** (109 questions) / **38 validation** (11 questions).

## Three separate sets

| Set | Source | Purpose |
|---|---|---|
| train | ~90% of the YAML questions | teach the model |
| validation | ~10% of the YAML questions | pick the best epoch; quick before/after check |
| **test** | the 20 scenario questions of the thesis + the 100 test questions — **never in a YAML here** | the numbers reported in the thesis |

## What the checker can and cannot catch

`check_dataset.py` proves a label is **valid**: a real category, an attribute that exists, one of the sixteen states, a name that appears in the question, SQL the agent's validator accepts, an up-to-date prompt, no duplicates or contradictions. It cannot prove a label is **right** — a question about Hessen labelled `Bayern` passes, because Bayern is a valid state. That is what the spot-check in step 4 is for.
