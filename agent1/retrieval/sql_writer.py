"""
SqlWriter — the one place this agent's SQL comes from.

The category is already known (QueryClassifier) and the parameters are
already extracted (QueryExtractor), so writing SQL needs no hand-written
method per query shape. The model gets the user's question plus the
parameters as JSON, and the category + step pick which prompt it sees:

    config/prompts/sql/rules.yaml           intro, schema header, rules (shared)
    config/prompts/sql/<category>.yaml      task, placeholders, output columns
                                            and worked examples, per step

Three rules keep the model honest:

  1. The model writes only the SQL text. Every value (names, years, WKT,
     distances) is bound by Python under the placeholder names the prompt
     lists, so the model cannot drop, add or change one.
  2. Every statement passes validate_sql() before it runs: one read-only
     SELECT on allowlisted tables and columns, no forbidden functions.
  3. The result must carry the output columns the caller reads by name
     (run() checks this), so a wrong alias fails loudly instead of silently.

Running this against a database role with SELECT-only privileges on these
tables remains the strongest guarantee; validate_sql() is one layer of
defence, not the only one that should exist.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import openai
import sqlglot
import yaml
from sqlalchemy import text
from sqlglot import exp

from ..database import SessionLocal

log = logging.getLogger("agent1.retrieval.sql_writer")

SQL_MODEL = os.getenv("SQL_MODEL", "gpt-4o-mini")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCHEMA_DIR = _REPO_ROOT / "config" / "schema"
_SQL_PROMPTS = _REPO_ROOT / "config" / "prompts" / "sql"

_ENTITIES: dict = yaml.safe_load((_SCHEMA_DIR / "entities.yaml").read_text(encoding="utf-8"))["entities"]
_ATTRIBUTE_TABLES: list = yaml.safe_load(
    (_SCHEMA_DIR / "attributes.yaml").read_text(encoding="utf-8")
)["attribute_tables"]
_RULES: dict = yaml.safe_load((_SQL_PROMPTS / "rules.yaml").read_text(encoding="utf-8"))

# A :name placeholder, but not the second colon of a `::type` cast.
_PLACEHOLDER = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMA — what tables/columns exist, for the prompt and for the validator
# ═══════════════════════════════════════════════════════════════════════════

def _entity_columns(entity: dict) -> Set[str]:
    """Every column one entities.yaml entry (e.g. "state" or "city") declares:
    its key/id/geometry columns, plus lat/lng if it's a point entity."""
    cols = {entity["key_column"], entity["id_column"], entity["geometry_column"]}
    if "lat_column" in entity:
        cols.add(entity["lat_column"])
    if "lng_column" in entity:
        cols.add(entity["lng_column"])
    return cols


def _attribute_table_columns(table: dict) -> Set[str]:
    """Every column one attributes.yaml table declares: its join column
    (the FK back to the entity it's about), its period column if it has
    one, and each of its actual data columns."""
    cols = {table["join_column"]}
    if table.get("period_column"):
        cols.add(table["period_column"])
    cols.update(table["columns"].keys())
    return cols


def allowed_tables_and_columns() -> Dict[str, Set[str]]:
    """{table_name: {every column name a query may reference in that table}}
    — the whitelist validate_sql() checks generated SQL against. A disabled
    entity (entities.yaml's `enabled: false`) is left out, same as it's
    excluded everywhere else in this codebase."""
    allowed: Dict[str, Set[str]] = {}
    for entity in _ENTITIES.values():
        if not entity.get("enabled", True):
            continue
        allowed.setdefault(entity["table"], set()).update(_entity_columns(entity))
    for table in _ATTRIBUTE_TABLES:
        allowed.setdefault(table["table"], set()).update(_attribute_table_columns(table))
    return allowed


def schema_description() -> str:
    """Human-readable table/column list for the LLM prompt — describes only
    what's actually queryable, so the model has an accurate map instead of
    guessing column names that don't exist."""
    lines = []
    for entity in _ENTITIES.values():
        if not entity.get("enabled", True):
            continue
        cols = sorted(_entity_columns(entity))
        lines.append(f"- {entity['table']} ({entity['label_plural']}): {', '.join(cols)}")
    for table in _ATTRIBUTE_TABLES:
        cols = sorted(_attribute_table_columns(table))
        lines.append(
            f"- {table['table']} ({table['entity']} attributes, "
            f"join to the {table['entity']} table on {table['join_column']}): "
            f"{', '.join(cols)}"
        )
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SAFETY — is a statement the model wrote actually safe to run?
# ═══════════════════════════════════════════════════════════════════════════

# Functions with no legitimate role in a plain data SELECT for this system,
# and a real one in an attack: reading arbitrary files, sleeping (blind
# timing exfiltration / DoS), reaching another database, running a shell
# command, or altering server state. Checked by name, case-insensitively,
# regardless of which of the tables/columns checks above would also have
# caught the surrounding query — a second, independent net.
_FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_sleep_for", "pg_sleep_until",
    "pg_read_file", "pg_read_binary_file", "pg_ls_dir", "pg_stat_file",
    "lo_import", "lo_export", "lo_read", "lo_write",
    "dblink", "dblink_connect", "dblink_exec",
    "copy_from_program", "copy_to_program",
    "pg_terminate_backend", "pg_cancel_backend",
    "pg_reload_conf", "set_config", "current_setting",
    "query_to_xml", "xpath",
}


class UnsafeSQLError(ValueError):
    """Raised when generated SQL fails validation. Always raised, never
    swallowed by a caller — there is no partial-trust way to run SQL that
    failed this check."""


def validate_sql(sql: str) -> None:
    """Raise UnsafeSQLError if `sql` is not a single, read-only SELECT
    referencing only allowlisted tables, columns, and functions. Returns
    normally (does nothing) if every check passes.

    Uses a real SQL parser (sqlglot) rather than regex/string matching —
    regex-based SQL filtering is well known to be bypassable via comments,
    string literals, whitespace, and encoding tricks that still parse as
    valid SQL a person didn't anticipate a pattern for."""
    # Pre-check, ahead of check 1: reject comments on the raw text itself,
    # before any parsing happens — a mismatch between how this validator's
    # parser and Postgres's own parser handle an edge case is its own
    # vulnerability class (a "parser differential"), and a comment has no
    # legitimate purpose in a generated data query anyway.
    if "--" in sql or "/*" in sql:
        raise UnsafeSQLError("Comments are not allowed in generated SQL.")

    # Check 1: the text has to parse as SQL at all.
    try:
        parsed = sqlglot.parse(sql, read="postgres")
    except Exception as exc:
        raise UnsafeSQLError(f"SQL failed to parse: {exc}") from exc

    # Check 2: exactly one statement — sqlglot.parse() splits on ';', so
    # "SELECT ...; DROP TABLE ...;" comes back as two statements here.
    statements = [s for s in parsed if s is not None]
    if len(statements) != 1:
        raise UnsafeSQLError(
            f"Expected exactly one SQL statement, got {len(statements)} — "
            f"statement stacking is rejected outright."
        )
    stmt = statements[0]

    # Check 3: SELECT only, and not SELECT ... INTO (which creates a table
    # as a side effect of what looks like a plain read).
    if not isinstance(stmt, exp.Select):
        raise UnsafeSQLError(
            f"Only SELECT statements are allowed; got {type(stmt).__name__}."
        )
    if stmt.args.get("into") is not None:
        raise UnsafeSQLError("SELECT ... INTO is rejected — it creates a table.")

    allowed = allowed_tables_and_columns()

    # A CTE's own name (`WITH geoms AS (...)`) is a local label the query
    # defines and reads back within itself, never a real database
    # identifier — so it doesn't belong in, or need to pass, the table
    # allowlist below. Excluding it by name doesn't relax anything: every
    # real table actually read to produce that local data is still walked
    # and checked exactly like any other reference, since find_all()
    # traverses the whole tree including inside a CTE's own definition —
    # and a real table sharing a CTE's name could never be *reached* by
    # that name once the CTE shadows it for the rest of the statement, so
    # excluding it opens no path to an unauthorized table.
    cte_names = {c.alias for c in stmt.find_all(exp.CTE)}

    # Check 4: every table referenced anywhere in the statement (including
    # inside a JOIN, a subquery, or a CTE — find_all() walks the whole tree)
    # must be one this system itself declares, or a CTE this same statement
    # defines.
    referenced_tables = {t.name for t in stmt.find_all(exp.Table)} - cte_names
    unknown_tables = referenced_tables - set(allowed)
    if unknown_tables:
        raise UnsafeSQLError(
            f"Query references table(s) not in the allowed schema: {sorted(unknown_tables)}."
        )

    # Check 5a: same for every column — but a CTE's or a derived table's own
    # declared output-column names (`... AS t(col1, col2)`, a CTE's own
    # `name(col1, col2)` form included) are local labels too, not real
    # database columns, so a reference to one shouldn't need to match the
    # schema allowlist either.
    #
    # That exemption has to be scoped precisely, not just "this name was
    # declared as a local alias *somewhere* in the statement" — a flat,
    # query-wide exemption would let an unrelated, genuinely-forbidden
    # column slip through anywhere it happens to share a name with some
    # CTE's own declared output column, e.g.:
    #   WITH x(internal_notes) AS (SELECT state_name FROM states)
    #   SELECT r.internal_notes FROM state_demographics r, x
    # `r.internal_notes` has nothing to do with `x` — it's a real,
    # unqualified-would-be-forbidden column read off an unrelated table —
    # and must still be rejected even though "internal_notes" also happens
    # to be x's own column name. So a column is only exempt when the
    # *specific reference* actually resolves to that local construct:
    # qualified by its alias (`g1.shape` where g1 is a usage of the "geoms"
    # CTE), or unqualified and inside the one SELECT scope where that
    # source is directly in FROM/JOIN (the CTE's own body reading its
    # UNNEST'd source unqualified, for instance) — never by bare name
    # anywhere in the statement.
    all_allowed_columns = {col for cols in allowed.values() for col in cols}

    # {CTE name: the output columns it declares} — needed to resolve a
    # second local alias on a re-reference (`FROM geoms g1 JOIN geoms g2`)
    # back to the same declared column set.
    cte_columns: Dict[str, Set[str]] = {}
    for cte in stmt.find_all(exp.CTE):
        alias_node = cte.args.get("alias")
        cols = {ident.name for ident in (alias_node.args.get("columns") or [])} if alias_node else set()
        if cols:
            cte_columns[cte.alias] = cols

    # {local alias name: columns it's allowed to expose under that alias} —
    # covers a construct's own declared alias (a CTE's `geoms(...)`, an
    # UNNEST's `t(...)`) and any further alias a CTE picks up on reuse
    # (`g1`/`g2` above), which carry no columns list of their own but
    # expose exactly the CTE's.
    alias_exposed: Dict[str, Set[str]] = {}
    for alias_node in stmt.find_all(exp.TableAlias):
        cols = {ident.name for ident in (alias_node.args.get("columns") or [])}
        if cols:
            alias_exposed[alias_node.this.name] = cols
    for t in stmt.find_all(exp.Table):
        if t.name in cte_columns:
            alias_exposed[t.alias or t.name] = cte_columns[t.name]

    def _owning_select(node: exp.Expression):
        """Nearest enclosing SELECT — the only scope an unqualified column
        can legally resolve a same-scope FROM source's column against."""
        parent = node.parent
        while parent is not None and not isinstance(parent, exp.Select):
            parent = parent.parent
        return parent

    def _local_names_in_scope(select_node: exp.Select) -> Set[str]:
        """Column names visible unqualified inside `select_node`, from a
        local (CTE or derived-table) source directly in its own FROM/JOIN —
        not inherited from any outer or unrelated SELECT."""
        names: Set[str] = set()
        from_clause = select_node.args.get("from_")
        sources = [from_clause.this] if from_clause else []
        sources += [j.this for j in select_node.args.get("joins") or []]
        for src in sources:
            if isinstance(src, exp.Table) and src.name in cte_columns:
                names |= cte_columns[src.name]
                continue
            src_alias = src.args.get("alias") if hasattr(src, "args") else None
            if src_alias is not None:
                names |= {ident.name for ident in (src_alias.args.get("columns") or [])}
        return names

    def _is_locally_exempt(column: exp.Column) -> bool:
        if column.table:
            return column.name in alias_exposed.get(column.table, set())
        enclosing = _owning_select(column)
        return enclosing is not None and column.name in _local_names_in_scope(enclosing)

    unknown_columns = {
        c.name
        for c in stmt.find_all(exp.Column)
        if c.name not in all_allowed_columns and not _is_locally_exempt(c)
    }
    if unknown_columns:
        raise UnsafeSQLError(
            f"Query references column(s) not in the allowed schema: {sorted(unknown_columns)}."
        )

    # Check 5b: every function call, against the denylist above — a second,
    # independent net even for a function that happens to pass checks 4/5a
    # (e.g. dblink() takes no table/column argument at all).
    called_functions = {
        f.name.lower()
        for f in stmt.find_all((exp.Func, exp.Anonymous))
        if getattr(f, "name", None)
    }
    forbidden_used = called_functions & _FORBIDDEN_FUNCTIONS
    if forbidden_used:
        raise UnsafeSQLError(f"Query calls forbidden function(s): {sorted(forbidden_used)}.")


# ═══════════════════════════════════════════════════════════════════════════
# WRITING — question + parameters + category/step in, one validated SELECT out
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BuiltQuery:
    """A statement ready to run, plus the readable form for the log."""
    sql: str                    # bound form, :named placeholders
    params: Dict[str, Any]      # values Python binds to those placeholders
    readable: str               # same statement with values written in, for logging only
    label: str = ""             # what this statement is for


class SqlWriter:
    """Writes one validated SELECT per call, for any category and step."""

    def __init__(self, client: openai.OpenAI | None = None, model: str = SQL_MODEL):
        self._client = client or openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
        self.tokens_used = 0
        self._prompts: Dict[str, str] = {}

    def _system_prompt(self, category: str, step: str) -> str:
        """rules.yaml + this category's step (task, placeholders, columns,
        examples). Built once per (category, step)."""
        key = f"{category}:{step}"
        if key in self._prompts:
            return self._prompts[key]

        path = _SQL_PROMPTS / f"{category.lower()}.yaml"
        if not path.exists():
            raise ValueError(f"No SQL prompt for category {category!r} — add {path}.")
        steps = yaml.safe_load(path.read_text(encoding="utf-8"))["steps"]
        if step not in steps:
            raise ValueError(f"{path.name} has no step {step!r} (has: {sorted(steps)}).")
        spec = steps[step]

        placeholders = "\n".join(f"  - :{name} — {desc}" for name, desc in spec["placeholders"].items())
        examples = "\n\n".join(
            "Input: " + json.dumps(ex["input"], ensure_ascii=False)
            + "\n→ " + json.dumps(ex["output"], ensure_ascii=False)
            for ex in spec["examples"]
        )
        rules = "\n".join(f"  - {rule}" for rule in _RULES["rules"])

        prompt = "\n\n".join([
            _RULES["intro"],
            _RULES["schema_intro"] + "\n\n" + schema_description(),
            _RULES["rules_intro"] + "\n" + rules,
            "TASK: " + spec["task"],
            "PLACEHOLDERS — bound by the caller. Use only these, spelled exactly "
            "like this:\n" + placeholders,
            "OUTPUT COLUMNS: " + spec["columns"],
            'Return ONLY {"sql": "<the statement>"}.',
            "EXAMPLES:\n\n" + examples,
        ]) + "\n"
        self._prompts[key] = prompt
        return prompt

    def write(self, question: str, category: str, step: str, shown: Dict[str, Any],
              bind: Dict[str, Any], label: str = "", previous_error: str = "") -> BuiltQuery:
        """Ask the model for one statement.

        `shown` is what the model sees besides the question (the extracted
        parameters that matter for this step); `bind` is what Python binds to
        the placeholders when the statement runs. `previous_error`, when set,
        tells the model why its last statement for this same request failed.
        Raises UnsafeSQLError or ValueError rather than ever returning a
        statement that failed a check."""
        payload = {"question": question, **shown}
        if previous_error:
            payload["previous_attempt_failed_with"] = previous_error
        user = json.dumps(payload, ensure_ascii=False, default=str)
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self._system_prompt(category, step)},
                {"role": "user", "content": user},
            ],
        )
        raw = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else 0
        self.tokens_used += tokens
        log.info("       | SqlWriter (%s, %s/%s, tokens=%d): %s", self.model, category, step, tokens, raw)

        try:
            sql = json.loads(raw).get("sql", "")
        except json.JSONDecodeError as exc:
            raise ValueError(f"SqlWriter response was not JSON: {raw!r}") from exc
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError(f"SqlWriter response had no 'sql': {raw!r}")

        validate_sql(sql)
        unknown = set(_PLACEHOLDER.findall(sql)) - set(bind)
        if unknown:
            raise ValueError(f"SQL uses placeholder(s) the caller does not bind: {sorted(unknown)}")

        return BuiltQuery(sql=sql, params=bind, readable=_readable(sql, bind),
                          label=label or f"{category}/{step}")


_writer: SqlWriter | None = None


def writer() -> SqlWriter:
    """The process-wide SqlWriter (built on first use, so importing this
    module needs no API key)."""
    global _writer
    if _writer is None:
        _writer = SqlWriter()
    return _writer


def write_and_run(question: str, category: str, step: str, shown: Dict[str, Any], bind: Dict[str, Any],
                  required: Iterable[str], queries: List[str], label: str = "") -> List[Dict[str, Any]]:
    """Write a statement, run it, return its rows. If the statement fails a
    check or the database rejects it, the error goes back to the model once
    so it can correct itself; a second failure is raised."""
    error = ""
    for attempt in (1, 2):
        try:
            built = writer().write(question, category, step, shown, bind, label, previous_error=error)
            return run(built, required, queries)
        except Exception as exc:                    # noqa: BLE001 — retried once, then raised
            if attempt == 2:
                raise ValueError(f"SQL for {category}/{step} failed twice: {exc}") from exc
            error = str(exc).split("\n[SQL:")[0][:500]
            log.warning("       | SQL for %s/%s failed, asking the model to correct it: %s", category, step, error)


def run(built: BuiltQuery, required: Iterable[str], queries: List[str]) -> List[Dict[str, Any]]:
    """Run a statement on this agent's own database and return its rows as
    dicts. `required` are the output columns the caller reads; a result
    missing one is an error. The readable SQL is appended to `queries`."""
    queries.append(built.readable)
    log.info("       | SQL > %s\n%s", built.label, built.readable)
    db = SessionLocal()
    try:
        result = db.execute(text(built.sql), built.params)
        columns = list(result.keys())
        rows = [dict(row._mapping) for row in result.fetchall()]
    finally:
        db.close()
    missing = [c for c in required if c not in columns]
    if missing:
        raise ValueError(f"Generated SQL ({built.label}) did not return column(s) {missing}; got {columns}")
    log.info("       | Rows returned: %d", len(rows))
    return rows


def _readable(sql: str, bind: Dict[str, Any]) -> str:
    """The statement with values written in, for the log only — never run.
    Long strings (WKT) are shortened so a log line stays readable."""
    def lit(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, str):
            return f"'{value}'" if len(value) <= 60 else f"'{value[:40]}...'[{len(value)} chars]"
        return str(value)

    out = sql
    for name in sorted(bind, key=len, reverse=True):
        value = bind[name]
        literal = ("ARRAY[" + ", ".join(lit(v) for v in value) + "]") if isinstance(value, list) else lit(value)
        out = re.sub(rf"(?<![:\w]):{name}\b", lambda _m: literal, out)
    return out + ";"
