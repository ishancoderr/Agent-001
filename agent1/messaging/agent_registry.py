"""
Central registry of peer agents.
Add AGENT3_URL, AGENT4_URL, … to .env to scale to N agents with no code changes.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

AGENT_REGISTRY: Dict[str, str] = {
    name: url
    for name, url in {
        "Agent-2": os.getenv("AGENT2_URL", "http://localhost:8001"),
        "Agent-3": os.getenv("AGENT3_URL", ""),
        "Agent-4": os.getenv("AGENT4_URL", ""),
    }.items()
    if url
}
