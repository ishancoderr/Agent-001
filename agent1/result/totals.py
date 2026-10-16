"""
Totals across places — "the combined population of Hessen and Thüringen",
"the population of Bayern and Berlin merged into one area".

A total is made per year and attribute, and only when every place has a value
for that year. A year where one place is missing gets no total: the values
that do exist are still returned, and the missing places are named. Adding up
only the part that is there would report a wrong number as if it were the
answer, and filling the gap from a neighbouring year would invent data.

Which attributes may be combined, and how, comes from
config/schema/attributes.yaml (`aggregate:` on a column) — a count adds up,
a rate or a density would not.
"""
from __future__ import annotations

from typing import Any, Dict, List

from kqml_messaging import response_status

# How each aggregate kind named in attributes.yaml combines the values.
AGGREGATE_FUNCTIONS = {"sum": sum}


def year_totals(merged: List[Dict[str, Any]], years: List[int], attributes: List[str],
                kind: str) -> List[Dict[str, Any]]:
    """One entry per (year, attribute): the total when every place has a
    value, else no total and the places that are missing."""
    places = list(dict.fromkeys(row["spatial"] for row in merged))
    combine = AGGREGATE_FUNCTIONS[kind]
    out = []
    for year in years:
        rows = {row["spatial"]: row for row in merged if row.get("year") == year}
        for attr in attributes:
            values = {place: (rows.get(place) or {}).get(attr) for place in places}
            missing = [place for place, value in values.items() if value is None]
            out.append({
                "year":      year,
                "attribute": attr,
                "aggregate": kind,
                "places":    places,
                "total":     None if missing else combine(values.values()),
                "missing":   missing,
                "status":    response_status(has_found=len(missing) < len(places), has_missing=bool(missing)),
            })
    return out


def full_total_years(merged: List[Dict[str, Any]], attributes: List[str], kind: str) -> List[int]:
    """The years in `merged` for which every place has every attribute — the
    years a full total can be given for."""
    years = sorted({row["year"] for row in merged})
    return [year for year in years
            if all(t["total"] is not None for t in year_totals(merged, [year], attributes, kind))]
