"""
Build fine-tuning examples from a questions YAML (default: questions_v1.yaml).

    1 question -> 1 classify example
               -> 1 extract example       (not for UNRELATED)
               -> every SQL step the pipeline runs for it (not for UNRELATED / NEEDS_YEAR)
               -> the SQL this agent runs when the PEER asks for it (peer: true)

The YAML holds only what a person decides: question, category, correct
extraction. Everything else is derived the way the pipeline does it — the
cleaned text classify/extract see (CleanQuery), the input every SQL step sees
(the same question/shown parameters gap_detector.py and spatial_compute.py
pass), the real system prompts (the real loaders) — and the gold SQL comes
from finetune/reference_sql.py. Every gold statement must pass validate_sql()
and bind only placeholders Python binds, or the build stops.

Outputs next to the YAML, named after it (questions_v1 -> questions_v1*.*):
    <name>.jsonl         every example ("messages" chat format + "meta")
    <name>_train.jsonl   the training split  (about 90%, by question)
    <name>_val.jsonl     the validation split (every 10th question per group)
    <name>.md            the same examples laid out for reading
    prompts/*.txt        each system prompt once, as the model sees it

Run from the repo root:  python -m finetune.build_examples [path/to/questions.yaml]
Then check it:           python -m finetune.check_dataset finetune/questions_v1.jsonl
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from agent1.pipeline.clean_query import CleanQuery
from agent1.pipeline.gazetteer import GERMAN_STATES, normalize_entity_name
from agent1.pipeline.prompt_loader import CLASSIFY_SYSTEM, EXTRACT_TEMPLATES
from agent1.retrieval.spatial_compute import _entity_type_for
from agent1.retrieval.sql_writer import _PLACEHOLDER, SqlWriter, validate_sql

from . import reference_sql as ref

HERE = Path(__file__).resolve().parent
PROMPTS = HERE / "prompts"
PEERS = ("Agent-1", "Agent-2")       # one shared model serves both agents, so both wordings

GROUPS = {"DIRECT_LOOKUP": "data", "GEOMETRY_LOOKUP": "geometry", "SPATIAL_OPERATION": "operation",
          "SPATIAL_ADJACENCY": "relationship", "SPATIAL_DIRECTION": "relationship",
          "SPATIAL_DISTANCE": "relationship", "SPATIAL_RELATIONSHIP_BUFFER": "delegation",
          "UNRELATED": "unrelated"}

_sql_writer = SqlWriter(client=object())        # only _system_prompt() is used — no API calls


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _pretty(obj: Dict[str, Any]) -> str:
    """One key per line, lists kept inline — easier to scan than indent=2."""
    body = ",\n".join(f"  {_json(k)}: {json.dumps(v, ensure_ascii=False, default=str)}" for k, v in obj.items())
    return "{\n" + body + "\n}"


# ═══════════════════════════════════════════════════════════════════════════
# One call = one training example
# ═══════════════════════════════════════════════════════════════════════════

def _call(title: str, prompt_name: str, system: str, user: str, answer: str,
          show_input: str, show_answer: str, input_lang: str, answer_lang: str,
          meta: Dict[str, Any]) -> Dict[str, Any]:
    return {"title": title, "prompt_name": prompt_name, "system": system, "user": user,
            "answer": answer, "show_input": show_input, "show_answer": show_answer,
            "input_lang": input_lang, "answer_lang": answer_lang, "meta": meta}


def classify_call(q: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = CleanQuery(q["question"]).cleaned
    answer = _json({"query_type": q["category"]})
    return _call("Classify", "classify", CLASSIFY_SYSTEM, cleaned, answer,
                 cleaned, answer, "text", "json", {"task": "classify", "category": q["category"]})


def extract_call(q: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = CleanQuery(q["question"]).cleaned
    system = EXTRACT_TEMPLATES[q["category"]] + f"\n\nCURRENT_YEAR = {date.today().year}"
    meta = {"task": "extract", "category": q["category"]}
    if q.get("expect"):
        meta["expect_query_type"] = q["expect"]
    if q.get("names_translated"):
        meta["names_translated"] = True
    return _call("Extract", f"extract_{q['category']}", system, f"Query: {cleaned}", _json(q["extract"]),
                 f"Query: {cleaned}", _pretty(q["extract"]), "text", "json", meta)


def sql_call(category: str, step: str, question: str, shown: Dict[str, Any],
             bind_keys: List[str], sql: str, title: str = "", note: str = "") -> Dict[str, Any]:
    validate_sql(sql)
    unknown = set(_PLACEHOLDER.findall(sql)) - set(bind_keys)
    if unknown:
        raise ValueError(f"{category}/{step}: gold SQL uses unbound placeholder(s) {sorted(unknown)}")
    payload = {"question": question, **shown}
    meta = {"task": "sql", "category": category, "step": step, "bind": sorted(bind_keys)}
    if note:
        meta["note"] = note
    return _call(title or f"SQL · {category} → {step}", f"sql_{category}_{step}",
                 _sql_writer._system_prompt(category, step),
                 json.dumps(payload, ensure_ascii=False, default=str), _json({"sql": sql}),
                 _pretty(payload), sql, "json", "sql", meta)


# ═══════════════════════════════════════════════════════════════════════════
# SQL steps per category — mirrors gap_detector.py / spatial_compute.py
# ═══════════════════════════════════════════════════════════════════════════

def shape_fetch_calls(entities: List[Tuple[str, str]], note: str = "") -> List[Dict[str, Any]]:
    """gap_detector.fetch_shapes(): one statement per entity type (in order of
    first appearance), stored names sorted, a neutral question."""
    by_type: Dict[str, List[str]] = {}
    for name, entity_type in entities:
        by_type.setdefault(entity_type, []).append(normalize_entity_name(name, entity_type))
    return [sql_call("GEOMETRY_LOOKUP", "fetch",
                     f"Fetch the stored shapes of these {entity_type} names: {sorted(set(names))}",
                     {"entity_type": entity_type, "spatial": sorted(set(names))}, ["names"],
                     ref.shape_fetch(entity_type), title=f"SQL · shape fetch ({entity_type})", note=note)
            for entity_type, names in by_type.items()]


def data_calls(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    ex, raw = q["extract"], q["question"]
    entity_type = ex.get("entity_type", "state")
    names = list(GERMAN_STATES) if ex["spatial"] == "all" else list(ex["spatial"])
    years, attributes = ex["temporal"], ex["attributes"]
    fetch_sql = ref.value_fetch(entity_type, attributes)
    shown = {"entity_type": entity_type, "spatial": names, "temporal": years, "attributes": attributes}
    calls = [sql_call("DIRECT_LOOKUP", "fetch", raw, shown, ["names", "years"], fetch_sql)]
    if q.get("presence"):
        places = q["presence"]
        calls.append(sql_call("DIRECT_LOOKUP", "presence",
                              f"Which of these {entity_type} names have any row at all: {places}",
                              {"entity_type": entity_type, "spatial": places}, ["names"],
                              ref.presence(entity_type, attributes),
                              note=f"runs only when the fetch found no rows for {places}"))
    if q.get("peer"):
        for peer in PEERS:
            calls.append(sql_call("DIRECT_LOOKUP", "fetch",
                                  f"{peer} asks for {', '.join(attributes)} of {', '.join(names)} in {years}",
                                  shown, ["names", "years"], fetch_sql, title=f"SQL · fetch (answering {peer})",
                                  note=f"this agent answering {peer}'s :missing-slots ask"))
    return calls


def operation_calls(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    ex, raw = q["extract"], q["question"]
    operation, names = ex["operation"], ex["spatial"]
    entity_type = ex.get("entity_type") or "state"
    if operation == "BufferWithin":
        entities = [(n, _entity_type_for(n, "city" if i == 0 else entity_type)) for i, n in enumerate(names)]
        return shape_fetch_calls(entities) + [
            sql_call("SPATIAL_OPERATION", "buffer_within", raw,
                     {"operation": operation, "spatial": names, "distance_km": float(ex.get("distance_km") or 100)},
                     ["ref_wkt", "ref_srid", "dist_m", "names", "wkts"], ref.BUFFER_WITHIN)]
    return shape_fetch_calls([(n, entity_type) for n in names]) + [
        sql_call("SPATIAL_OPERATION", "compute", raw, {"operation": operation, "spatial": names},
                 ["wkt_a", "srid_a", "wkt_b", "srid_b"], ref.operation(operation))]


def relationship_calls(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    """spatial_compute.resolve_relationship(): fetch the needed shapes, then
    one relationship statement (per reference — identical, so kept once)."""
    rel = q["extract"]["spatial_relationship"]
    kind = {"SPATIAL_ADJACENCY": "adjacency", "SPATIAL_DISTANCE": "distance"}.get(q["category"], rel["type"])
    subject = rel.get("subject")
    states = [normalize_entity_name(subject, "state")] if subject else list(GERMAN_STATES)
    refs = [(r, _entity_type_for(r, "city") if kind == "distance" else "state") for r in rel["refs"]]
    needed = list(dict.fromkeys([(s, "state") for s in states] + refs))
    wording = {"adjacency": "border", "distance": f"lie within {rel.get('distance_km')} km of"}.get(
        kind, f"lie {kind.replace('_of', '')} of")
    calls = shape_fetch_calls(needed)
    calls.append(sql_call(
        "SPATIAL_RELATIONSHIP", "compute", f"Which of the candidate states {wording} {', '.join(rel['refs'])}?",
        {"spatial_relationship": {"type": kind, "refs": rel["refs"], "subject": subject,
                                  "distance_km": rel.get("distance_km")}},
        ["names", "wkts", "ref", "ref_wkt", "ref_srid", "dist_m"], ref.relationship(kind)))
    if q["extract"].get("attributes"):
        calls[-1]["meta"]["note"] = ("the data fetch for the resulting states follows; it is the "
                                     "DIRECT_LOOKUP fetch pattern and depends on the map, so not generated here")
    return calls


def delegation_calls(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    ex, raw = q["extract"], q["question"]
    ref_name = normalize_entity_name(ex["spatial"][0], "city")
    distance_km = float(ex.get("distance_km") or 100)
    calls = shape_fetch_calls([(ex["spatial"][0], "city")]) + [
        sql_call("SPATIAL_RELATIONSHIP_BUFFER", "zone", raw, {"spatial": ex["spatial"], "distance_km": distance_km},
                 ["ref_wkt", "ref_srid", "dist_m"], ref.ZONE),
        sql_call("SPATIAL_RELATIONSHIP_BUFFER", "within", raw, {"target_entity": "city", "exclude": [ref_name]},
                 ["zone_wkt", "zone_srid", "exclude"], ref.within()),
    ]
    if q.get("peer"):
        for peer in PEERS:
            calls.append(sql_call("SPATIAL_RELATIONSHIP_BUFFER", "within",
                                  f"{peer} asks which of our cities lie inside this zone",
                                  {"target_entity": "city", "exclude": [ref_name]},
                                  ["zone_wkt", "zone_srid", "exclude"], ref.within(),
                                  title=f"SQL · within (answering {peer})",
                                  note=f"this agent testing its own cities for {peer}'s delegated zone"))
    return calls


SQL_STEPS = {"DIRECT_LOOKUP": data_calls,
             "GEOMETRY_LOOKUP": lambda q: shape_fetch_calls(
                 [(e["entity_name"], e["entity_type"]) for e in q["extract"]["entities"]]),
             "SPATIAL_OPERATION": operation_calls,
             "SPATIAL_ADJACENCY": relationship_calls, "SPATIAL_DIRECTION": relationship_calls,
             "SPATIAL_DISTANCE": relationship_calls,
             "SPATIAL_RELATIONSHIP_BUFFER": delegation_calls}


def calls_for(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    calls = [classify_call(q)]
    if q["category"] != "UNRELATED":
        calls.append(extract_call(q))
        if not q.get("expect"):                      # NEEDS_YEAR stops before any SQL
            calls += SQL_STEPS[q["category"]](q)
    unique, seen = [], set()
    for c in calls:                                  # a Union fold or two refs repeat one call
        key = (c["system"], c["user"], c["answer"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    for c in unique:
        c["meta"] = {"qid": q["id"], "group": GROUPS[q["category"]], "split": q["split"], **c["meta"]}
    return unique


def assign_splits(questions: List[Dict[str, Any]]) -> None:
    """Every 10th question of each group goes to validation, so every group
    is represented there and a question's examples never straddle the split."""
    position: Dict[str, int] = {}
    for q in questions:
        group = GROUPS[q["category"]]
        position[group] = position.get(group, 0) + 1
        q["split"] = "val" if position[group] % 10 == 0 else "train"


# ═══════════════════════════════════════════════════════════════════════════
# Output
# ═══════════════════════════════════════════════════════════════════════════

def write_jsonl(path: Path, calls: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for c in calls:
            fh.write(_json({"messages": [
                {"role": "system", "content": c["system"]},
                {"role": "user", "content": c["user"]},
                {"role": "assistant", "content": c["answer"]},
            ], "meta": c["meta"]}) + "\n")


def write_markdown(path: Path, source: Path, questions: List[Dict[str, Any]],
                   per_q: List[List[Dict[str, Any]]]) -> None:
    total = sum(len(c) for c in per_q)
    lines = [f"# Fine-tuning examples — {source.name}", "",
             f"{len(questions)} questions, {total} training examples. Generated — edit `{source.name}`, "
             "not this file.", "",
             "Each step is one line of the JSONL: the model gets the linked system prompt plus "
             "**Model sees**, and is trained to reply with **Model must answer**.", ""]
    current_group = None
    for q, calls in zip(questions, per_q):
        group = GROUPS[q["category"]]
        if group != current_group:
            lines += [f"# {group}", ""]
            current_group = group
        lines += [f"## {q['id']} · {q['category']}" + (" · validation" if q["split"] == "val" else ""), "",
                  f"> {q['question']}", "", "| # | Call | System prompt |", "|---|---|---|"]
        lines += [f"| {i} | {c['title']} | [{c['prompt_name']}.txt](prompts/{c['prompt_name']}.txt) |"
                  for i, c in enumerate(calls, 1)]
        lines.append("")
        for i, c in enumerate(calls, 1):
            lines += [f"### {i} · {c['title']}", ""]
            if c["meta"].get("note"):
                lines += [f"*{c['meta']['note']}*", ""]
            lines += ["**Model sees**", "", f"```{c['input_lang']}", c["show_input"], "```", "",
                      "**Model must answer**", "", f"```{c['answer_lang']}", c["show_answer"], "```", ""]
        lines.append("---\n")
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", nargs="?", default=str(HERE / "questions_v1.yaml"))
    source = Path(ap.parse_args().source).resolve()

    questions = yaml.safe_load(source.read_text(encoding="utf-8"))
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate question ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    assign_splits(questions)
    per_q = [calls_for(q) for q in questions]

    # Drop exact duplicates across questions (every "which states ..." question
    # fetches the same sixteen shapes). Training questions are kept first, so a
    # validation example never repeats one the model was trained on.
    seen, dropped = set(), 0
    for i in sorted(range(len(questions)), key=lambda i: questions[i]["split"] != "train"):
        kept = []
        for c in per_q[i]:
            key = (c["system"], c["user"], c["answer"])
            if key in seen:
                dropped += 1
            else:
                seen.add(key)
                kept.append(c)
        per_q[i] = kept
    calls = [c for cs in per_q for c in cs]

    stem = source.with_suffix("")
    write_jsonl(stem.with_suffix(".jsonl"), calls)
    write_jsonl(Path(f"{stem}_train.jsonl"), [c for c in calls if c["meta"]["split"] == "train"])
    write_jsonl(Path(f"{stem}_val.jsonl"), [c for c in calls if c["meta"]["split"] == "val"])
    PROMPTS.mkdir(exist_ok=True)
    for c in calls:
        (PROMPTS / f"{c['prompt_name']}.txt").write_text(c["system"], encoding="utf-8", newline="\n")
    write_markdown(stem.with_suffix(".md"), source, questions, per_q)

    n_val_q = sum(q["split"] == "val" for q in questions)
    n_val = sum(c["meta"]["split"] == "val" for c in calls)
    print(f"{len(questions)} questions -> {len(calls)} examples ({dropped} exact duplicates dropped) "
          f"(train {len(calls) - n_val} from {len(questions) - n_val_q} questions, "
          f"val {n_val} from {n_val_q} questions)")
    print(f"  {stem.name}.jsonl / _train.jsonl / _val.jsonl / .md, prompts/ "
          f"({len({c['prompt_name'] for c in calls})} files)")


if __name__ == "__main__":
    main()
