"""evaluator/settings.yaml, the answer key, and the agents' URLs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

SETTINGS: Dict[str, Any] = yaml.safe_load((HERE / "settings.yaml").read_text(encoding="utf-8"))

PORT: int = int(os.getenv("EVALUATOR_PORT") or SETTINGS["port"])
HOST: str = os.getenv("EVALUATOR_HOST") or SETTINGS.get("host", "127.0.0.1")
DATABASE = (HERE / (os.getenv("EVALUATOR_DATABASE") or SETTINGS["database"])).resolve()
TEST_SET = (HERE / (os.getenv("EVALUATOR_TEST_SET") or SETTINGS["test_set"])).resolve()
TIMEOUT_S: float = float(SETTINGS["request_timeout_s"])
RETRIES: Dict[str, Any] = SETTINGS["retries"]
FINGERPRINT: Dict[str, Any] = SETTINGS["fingerprint"]
EXTRACT_COMPARE: Dict[str, Any] = SETTINGS["extract_compare"]
PRICING: Dict[str, Dict[str, float]] = SETTINGS.get("pricing_usd_per_mtok") or {}
ESTIMATE: Dict[str, Any] = SETTINGS["estimate"]

# Agent roles: "primary" is asked every repeat, "peer" once (symmetry).
AGENTS: Dict[str, Dict[str, str]] = {
    role: {"name": a["name"], "url": (os.getenv(a.get("url_env", "")) or a["url"]).rstrip("/")}
    for role, a in SETTINGS["agents"].items()
}


def repeats_for(model: str) -> int:
    r = SETTINGS["repeats"]
    return int((r.get("per_model") or {}).get(model, r["default"]))


def load_questions() -> List[Dict[str, Any]]:
    """The answer key, in file order. Read on every call so an edit to the
    file shows without a restart."""
    questions = yaml.safe_load(TEST_SET.read_text(encoding="utf-8"))
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate ids in {TEST_SET.name}")
    return questions
