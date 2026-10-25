"""
How one answer is scored — all of it computed from the agent's response and
its trace (agent1/evaluation/trace.py), so it can be recomputed from the
stored responses whenever these rules change, without asking again.

- category:   the classify label vs the answer key
- extraction: the extracted fields vs the answer key, field by field
- SQL:        every SQL step passed the safety check / ran / did so first time
- answer:     a fingerprint of the final answer (see answer_view); equal
              fingerprints are the same answer — for consistency, symmetry and
              the hand-confirmed expected answer
- tokens, times, and how complex the question turned out to be
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from agent1.pipeline.gazetteer import _normalize_key, normalize_entity_name

from .config import CSV, EXTRACT_COMPARE, FINGERPRINT, PRICING

_IGNORE = set(FINGERPRINT["ignore_keys"])
_QUERY_KEYS = list(FINGERPRINT["query_keys"])
_DECIMALS = int(FINGERPRINT["decimals"])
_WKT_DECIMALS = int(FINGERPRINT["wkt_decimals"])
_NAME_FIELDS = set(EXTRACT_COMPARE["name_fields"])
_FIRST_MATTERS: Dict[str, List[str]] = EXTRACT_COMPARE.get("first_matters") or {}

_WKT = re.compile(r"^\s*(SRID=\d+;)?\s*(MULTI)?(POINT|LINESTRING|POLYGON|GEOMETRYCOLLECTION)\b", re.I)
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


# ═══════════════════════════════════════════════════════════════════════════
# The final answer
# ═══════════════════════════════════════════════════════════════════════════

def _shape(wkt: str) -> str:
    """A shape as its type and rounded vertex set: two answers that draw the
    same shape compare equal even when the SQL started a ring elsewhere."""
    kind = wkt.strip().split("(", 1)[0].split(";")[-1].strip().upper() or "GEOMETRY"
    nums = [round(float(n), _WKT_DECIMALS) for n in _NUMBER.findall(wkt.split(";", 1)[-1])]
    points = sorted(set(zip(nums[0::2], nums[1::2])))
    if len(points) <= 1:
        return f"{kind} {' '.join(f'{x:g} {y:g}' for x, y in points)}".strip()
    digest = hashlib.sha1(json.dumps(points).encode()).hexdigest()[:10]
    return f"{kind} [{len(points)} vertices #{digest}]"


def _canon(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canon(v) for k, v in sorted(value.items()) if k not in _IGNORE}
    if isinstance(value, list):
        items = [_canon(v) for v in value]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
    if isinstance(value, float):
        return round(value, _DECIMALS)
    if isinstance(value, str) and _WKT.match(value):
        return _shape(value)
    return value


def _short_wkt(value: Any) -> Any:
    """KQML messages for a CSV cell: long geometry text cut to its start and
    its number of points; everything else as it was sent."""
    if isinstance(value, dict):
        return {k: _short_wkt(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_short_wkt(v) for v in value]
    limit = int(CSV["wkt_max_chars"])
    if isinstance(value, str) and len(value) > limit and _WKT.match(value):
        points = len(_NUMBER.findall(value.split(";", 1)[-1])) // 2
        return f"{value[:limit]}… [{points} points]"
    return value


def kqml_messages(trace: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """The KQML messages of one ask, as JSON lists (one entry per exchange)."""
    exchanges = (trace.get("kqml") or {}).get("exchanges") or []
    cap = int(CSV["cell_max_chars"])
    out: Dict[str, Optional[str]] = {}
    for key, field in (("kqml_sent", "sent"), ("kqml_received", "received")):
        msgs = [_short_wkt(x.get(field)) for x in exchanges if x.get(field) is not None]
        text = json.dumps(msgs, ensure_ascii=False) if msgs else None
        out[key] = text if text is None or len(text) <= cap else text[:cap] + "… [cut]"
    return out


def answer_view(response: Dict[str, Any]) -> Dict[str, Any]:
    """What the answer says, without how it was produced: the status, the
    question type it was answered as, and everything else in the response
    except the ignored keys (settings.yaml `fingerprint`)."""
    query = response.get("query") or {}
    view: Dict[str, Any] = {"status": response.get("status"),
                            **{k: query.get(k) for k in _QUERY_KEYS}}
    for key, value in response.items():
        if key not in _IGNORE and key not in ("query", "status"):
            view[key] = _canon(value)
    return view


def fingerprint(view: Dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(view, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def error_fingerprint(http_status: Optional[int]) -> str:
    return f"error-{http_status or 'none'}"


def answer_summary(view: Dict[str, Any]) -> str:
    """One line for the CSV and the results table."""
    parts = [str(view.get("status"))]
    if view.get("type"):
        parts.append(str(view["type"]))
    if "verdict" in view and view["verdict"] is not None:
        parts.append(f"verdict={'yes' if view['verdict'] else 'no'}")
    data = view.get("data")
    rows = [r for v in data.values() for r in (v or [])] if isinstance(data, dict) else         (data if isinstance(data, list) else [])
    if rows:
        shown = []
        for r in rows[:8]:
            if not isinstance(r, dict):
                shown.append(str(r))
                continue
            place, year = r.get("spatial", ""), r.get("year", "")
            values = ", ".join(f"{k}={v}" for k, v in r.items() if k not in ("spatial", "year", "missing"))
            shown.append(f"{place} {year}: {values or 'no value'}".strip())
        parts.append("; ".join(shown) + (f"; … {len(rows) - 8} more rows" if len(rows) > 8 else ""))
    if view.get("totals"):
        parts.append("totals " + ", ".join(
            f"{t.get('year', '?')}:{t.get('attribute', '')}={t.get('total')}".replace(":=", "=")
            for t in view["totals"][:6]))
    if isinstance(view.get("matches"), list):
        names = [m.get("name") if isinstance(m, dict) else str(m) for m in view["matches"]]
        parts.append(f"{len(names)} matches" + (": " + ", ".join(map(str, names[:8])) if names else "")
                     + (" …" if len(names) > 8 else ""))
    if isinstance(view.get("geometries"), list):
        found = sum(1 for g in view["geometries"] if g.get("wkt"))
        parts.append(f"{found}/{len(view['geometries'])} shapes")
    if isinstance(view.get("result"), dict) and view["result"].get("wkt"):
        parts.append(str(view["result"]["wkt"]))
    if view.get("still_missing"):
        parts.append(f"missing {view['still_missing']}")
    return " · ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# Extraction vs the answer key
# ═══════════════════════════════════════════════════════════════════════════

def _empty(v: Any) -> bool:
    return v is None or v == [] or v == {} or v == ""


def _name(v: Any) -> Any:
    if not isinstance(v, str):
        return v
    return _normalize_key(normalize_entity_name(v.strip()))


def _number(v: Any) -> Any:
    f = float(v)
    return int(f) if f.is_integer() else f


def _norm(value: Any, field: str = "") -> Any:
    if isinstance(value, dict):
        return {k: _norm(v, k) for k, v in value.items() if not _empty(v)}
    if isinstance(value, list):
        items = [_norm(v, field) for v in value]
        if field == "spatial" and items == ["all"]:
            return "all"
        return items
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return _number(value)
    if isinstance(value, str):
        s = value.strip()
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return _number(s)
        if field in _NAME_FIELDS and s.lower() != "all":
            return _name(s)
        return s.casefold()
    return value


def _key(v: Any) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def _shown(v: Any) -> str:
    return "(none)" if _empty(v) else _key(v)


def _same(expected: Any, got: Any, field: str, ordered_first: bool) -> bool:
    if isinstance(expected, list) and isinstance(got, list):
        if sorted(map(_key, expected)) != sorted(map(_key, got)):
            return False
        return not (ordered_first and expected and _key(expected[0]) != _key(got[0]))
    if isinstance(expected, dict) and isinstance(got, dict):
        return not _diff(expected, got, "", [])
    return expected == got


def _diff(expected: Dict[str, Any], got: Dict[str, Any], category: str, prefix: List[str]) -> List[str]:
    out: List[str] = []
    first = set(_FIRST_MATTERS.get(category, []))
    for field in sorted(set(expected) | set(got)):
        e, g = expected.get(field), got.get(field)
        if _empty(e) and _empty(g):
            continue
        path = ".".join(prefix + [field])
        if isinstance(e, dict) and isinstance(g, dict):
            out += _diff(e, g, category, prefix + [field])
        elif not _same(e, g, field, field in first and not prefix):
            out.append(f"{path}: expected {_shown(e)}, got {_shown(g)}")
    return out


def compare_extraction(category: str, expected: Optional[Dict[str, Any]],
                       got: Optional[Dict[str, Any]]) -> Tuple[Optional[bool], List[str]]:
    """(True/False, differences) — or (None, []) when there is nothing to
    compare (UNRELATED in the key, or the agent never got to extraction)."""
    if expected is None:
        return None, []
    if got is None:
        return False, ["no extraction"]
    diffs = _diff(_norm(expected), _norm(got), category, [])
    return not diffs, diffs


# ═══════════════════════════════════════════════════════════════════════════
# Everything measured on one ask
# ═══════════════════════════════════════════════════════════════════════════

def _complexity(q: Dict[str, Any]) -> Dict[str, int]:
    """How much the question asks for, from the answer key: places named,
    years, attributes."""
    ex = q.get("extract") or {}
    rel = ex.get("spatial_relationship") or {}
    places = ex.get("spatial")
    n_places = (len(places) if isinstance(places, list) else 0) + len(ex.get("entities") or []) \
        + len(rel.get("refs") or []) + (1 if rel.get("subject") else 0)
    return {"n_places": n_places, "n_years": len(ex.get("temporal") or []),
            "n_attributes": len(ex.get("attributes") or [])}


def cost_usd(model: str, tokens_in: int, tokens_out: int, peer_tokens: int) -> Optional[float]:
    """The asked agent's tokens at the model's price; the peer reports only a
    total, priced at the same input/output mix."""
    price = PRICING.get(model)
    if price is None:
        return None
    own = tokens_in + tokens_out
    share_out = tokens_out / own if own else 0.0
    peer_in, peer_out = peer_tokens * (1 - share_out), peer_tokens * share_out
    return round(((tokens_in + peer_in) * price["input"] + (tokens_out + peer_out) * price["output"]) / 1e6, 6)


def score(q: Dict[str, Any], model: str, response: Optional[Dict[str, Any]],
          http_status: Optional[int]) -> Dict[str, Any]:
    """The flat measures stored with an ask (store.asks columns)."""
    expected = q.get("category")
    out: Dict[str, Any] = {"expected_category": expected, **_complexity(q)}
    if response is None or http_status != 200:
        out.update(fingerprint=error_fingerprint(http_status), answer_view=None,
                   answer_summary=f"HTTP {http_status}" if http_status else "no response")
        return out

    t = response.get("trace") or {}
    got_category = t.get("classify")
    out["category_got"] = got_category
    if not q.get("extract") and isinstance(t.get("extract"), dict):
        # No expected extraction: size the question by what the agent extracted.
        out.update(_complexity({"extract": t["extract"]}))
    # A question without an expected category (a free question set) leaves
    # the category and extraction checks blank; the answer is still judged by hand.
    if expected is not None:
        out["category_ok"] = int(got_category == expected) if got_category is not None else 0
        if got_category == expected:
            ok, diffs = compare_extraction(expected, q.get("extract"), t.get("extract"))
            out["extract_ok"] = None if ok is None else int(ok)
            out["extract_diff"] = "; ".join(diffs) or None

    steps = t.get("sql_steps") or []
    out["sql_steps"] = len(steps)
    if steps:
        out["sql_attempts"] = sum(s["attempts"] for s in steps)
        out["sql_first_try_ok"] = int(all(s["first_try_ok"] for s in steps))
        out["sql_passed_check"] = int(all(s["passed_check"] for s in steps))
        out["sql_ran"] = int(all(s["ran"] for s in steps))
        out["sql_errors"] = " | ".join(e for s in steps for e in s["errors"]) or None

    tokens = t.get("tokens") or {}
    kqml = t.get("kqml") or {}
    out["tokens_in"], out["tokens_out"] = tokens.get("input", 0), tokens.get("output", 0)
    out["peer_tokens"] = kqml.get("peer_tokens", 0)
    out["tokens_total"] = out["tokens_in"] + out["tokens_out"] + out["peer_tokens"]
    out["cost_usd"] = cost_usd(model, out["tokens_in"], out["tokens_out"], out["peer_tokens"])

    stages = t.get("llm_by_stage") or {}
    out["llm_calls"] = len(t.get("llm_calls") or [])
    out["models_used"] = ",".join(sorted({c["model"] for c in t.get("llm_calls") or []})) or None
    out["ms_agent"] = t.get("ms")
    for stage in ("classify", "extract", "sql"):
        out[f"ms_{stage}"] = (stages.get(stage) or {}).get("ms", 0.0)
    out["ms_kqml"] = kqml.get("ms", 0.0)
    out["kqml_turns"] = kqml.get("turns", 0)
    out.update(kqml_messages(t))

    view = answer_view(response)
    out["answer_status"] = response.get("status")
    out["answer_type"] = (response.get("query") or {}).get("type")
    out["answer_view"] = json.dumps(view, sort_keys=True, ensure_ascii=False)
    out["fingerprint"] = fingerprint(view)
    out["answer_summary"] = answer_summary(view)
    return out


def consistency(fingerprints: List[str]) -> Optional[float]:
    """Share of the asks that gave the most common answer."""
    if not fingerprints:
        return None
    return Counter(fingerprints).most_common(1)[0][1] / len(fingerprints)
