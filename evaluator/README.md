# Evaluator

The test runner behind the workbench's **Evaluation** tab. It asks the agents
the test questions with each chosen model, scores every answer, keeps
everything in a SQLite file, and gives it all back as CSV.

```
browser ──/api/eval──► evaluator :8002 ──POST /query {"llm", "trace": true}──► Agent-001 :8000 ◄─KQML─► Agent-002 :8001
                         │                                                    (symmetry: the same question, once, to Agent-002)
                         └── evaluator/data/evaluation.sqlite
```

It lives only in this repository (like `finetune/`); Agent-002 needs nothing
beyond the `trace` support it already has.

## Run it

In the workbench: **Evaluation tab → Start evaluator**. Agent-001 starts it as
a separate background process (`agent1/evaluation/evaluator_launcher.py`,
output in `logs/evaluator.log`); it keeps running when Agent-001
reloads or stops, and **Stop evaluator** ends it. Or from a terminal:

```bash
cd D:\Agent-001
venv\Scripts\activate
python -m evaluator            # http://127.0.0.1:8002, reached through the workbench
```

Both agents must be running. The workbench's dev server proxies `/api/eval`
to it (`proxy.conf.json`; restart `npm start` after pulling that change).
Nothing to configure: it checks your workbench login with the agents'
`AUTH_SECRET` (read from `agent1/.env`) and asks the agents **as the user who
started the run**, so the agents' logs and `evaluation_metrics.log` show who
ran it, and a run of many hours does not depend on the browser staying open.

Settings: `evaluator/settings.yaml` (agents' URLs, the answer key, default
repeats per model, retries, how answers are compared, **prices** and the
estimate). Optional `evaluator/.env`: `AGENT1_URL`, `AGENT2_URL`,
`EVALUATOR_PORT`, `EVALUATOR_HOST`, `EVALUATOR_TEST_SET`, `EVALUATOR_DATABASE`.

## What is measured

Every ask is sent with `"trace": true`; the agent then returns a step-by-step
record (`agent1/evaluation/trace.py`) next to the answer. From it:

| Measure | How |
|---|---|
| **Category** | the classify label = `category` in `finetune/test_set_v2.yaml` |
| **Extraction** | the extracted fields = `extract` in the key, field by field: case and list order ignored, place names compared after the agent's own name normalisation, empty = missing; for Difference / BufferWithin the first place must match too. `extract_diff` names every difference |
| **SQL** | every SQL step passed the safety check and ran — first time (`sql_first_try_ok`) and after the one retry (`sql_passed_check`, `sql_ran`); the errors are kept |
| **Final answer** | the answer is reduced to a *fingerprint* (below). You confirm each distinct answer once in the tab — ✓ or ✗ — and that verdict holds for every ask, model, agent and run that gave the same answer. Until then the tab suggests a verdict: "differs from the confirmed answer" or "no confirmed answer yet". An HTTP error counts as wrong |
| **Tokens** | input and output tokens of every LLM call on the asked agent, plus the tokens the peer spent answering its KQML asks (with the same model — the ask carries it). Cost = tokens × `pricing_usd_per_mtok` |
| **Response time** | the whole question as the evaluator saw it (`wall_ms`), the agent's own total, and per step: classify, extract, SQL, KQML round trips. Every single call is in `steps.csv`; `n_places`, `n_years`, `n_attributes`, `sql_steps`, `kqml_turns` describe the question's complexity |
| **Consistency** | each question is asked *repeats* times (5 by default, 1 for GPT-4 and Claude Opus — `settings.yaml`); consistency = share of the repeats that gave the most common answer |
| **Symmetry** | each question is also sent once to Agent-002; symmetric = its answer equals Agent-001's first answer |

**The fingerprint.** Two answers are the same when they say the same thing:
timings, tokens, request ids and *which agent supplied a row* are dropped
(they differ between two correct answers — a row is labelled `Agent-1+Agent-2`
on one agent and `Agent-2+Agent-1` on the other), numbers are rounded, lists
are compared regardless of order, and a shape is compared by its type and
rounded vertex set. The keys and decimals are in `settings.yaml`
`fingerprint`.

## In the tab

1. **Step 1 · models** — tick the models (their ids are shown under the
   names), set the repeats per model and symmetry on/off.
2. **Step 2 · question set** — paste or upload a JSON list:

   ```json
   [
     {"question": "What was the population of Hessen in 2019?", "model": "gpt-4o-mini"},
     {"question": "Which states border Bayern?", "model": ["gpt-4o", "claude-haiku"]},
     {"question": "Which cities are within 30 km of Leipzig?"}
   ]
   ```

   | Field | |
   |---|---|
   | `question` | required |
   | `model` | a model id (or label) from step 1, a list of them, or left out / `"all"` = every ticked model. Naming a model that is not ticked is an error |
   | `id` | optional; otherwise made from the question text, so the same question keeps its id and its confirmed answers across runs |
   | `category`, `extract` | optional: the expected classify label and extraction, in the format of `finetune/questions_vN.yaml`. Without them the category and extraction checks stay blank and the answer is judged by hand only. A question that is in the answer key (`test_set` in settings.yaml) gets its labels from there |

   "Load test set" fills the box with the answer key's questions; "Insert
   example" writes the format above with the ticked models.
3. **Step 3 · run** — the estimate (asks, cost, time; measured averages once a
   model has run) and Start. Each model runs its questions in turn: per
   question its repeats on Agent-001, then once on Agent-002.
4. **Runs** — progress, the question being asked, time left, pause / resume /
   cancel. One run goes at a time (others queue), so response times are not
   distorted. A run continues if the page is closed; if the evaluator stops,
   it carries on where it was when restarted. If an agent stays unreachable
   the run pauses with the reason.
5. **Results** — the per-model table for the ticked runs, per question below.
6. **Downloads — one CSV per model**: `evaluation_<model>_runs-N.csv`, one row
   per ask (question × repeat × agent) with the answer, its verdict, the
   category / extraction / SQL checks, tokens, cost and times, and on every
   row the question's consistency and symmetry. "All models (.zip)" holds every
   model's file plus the summary per model. Under "more downloads":
   `asks.csv`, `questions.csv`, `models.csv`, `categories.csv`, `steps.csv`
   (every LLM call, SQL attempt, KQML trip), `verdicts.csv`. UTF-8 with BOM,
   so Excel shows ü and ß.
7. **Confirm the answers** — every distinct answer per question, with the
   models and agents that gave it, the difference to the confirmed answer, and
   ✓ / ✗ and a note.

Changed a label in the answer key, or a rule in `settings.yaml`? `POST
/runs/{id}/rescore` scores the stored responses again — no new asks.

## The test set

`finetune/test_set_v2.yaml` holds the expected category and extraction of the
100 questions in `test_set_v2.txt` (the same ids, t001–t100). It is the
research test set: never train on it or tune the agents to its results. It is
validated like the training files (in a scratch copy, so no training files
are written):

```bash
copy finetune\test_set_v2.yaml %TEMP%\check\
python -m finetune.build_examples %TEMP%\check\test_set_v2.yaml
python -m finetune.check_dataset  %TEMP%\check\test_set_v2.jsonl
```

`build_examples` also rewrites `finetune/prompts/` — harmless (it writes
today's prompts), but the check is only about the labels.
