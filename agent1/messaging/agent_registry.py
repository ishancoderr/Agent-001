"""
Who this agent is, and which peer agents it can ask — all from .env.

    AGENT_NAME=Agent-1
    PEER_AGENTS=Agent-2=http://localhost:8001,Agent-3=http://localhost:8002

No agent name or URL is written in code, so every agent runs the same code
with its own .env, and adding a peer is one entry in PEER_AGENTS. The first
peer listed is the one asked for missing data (PRIMARY_PEER).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

AGENT_NAME: str = os.getenv("AGENT_NAME", "").strip()
if not AGENT_NAME:
    raise RuntimeError("AGENT_NAME is not set — add e.g. AGENT_NAME=Agent-1 to this agent's .env")


def _parse_peers(raw: str) -> Dict[str, str]:
    peers: Dict[str, str] = {}
    for entry in filter(None, (part.strip() for part in raw.split(","))):
        name, sep, url = entry.partition("=")
        if not sep or not name.strip() or not url.strip():
            raise RuntimeError(f"PEER_AGENTS entry {entry!r} is not name=url")
        peers[name.strip()] = url.strip()
    return peers


AGENT_REGISTRY: Dict[str, str] = _parse_peers(os.getenv("PEER_AGENTS", ""))
AGENT_REGISTRY.pop(AGENT_NAME, None)          # an agent never asks itself
if not AGENT_REGISTRY:
    raise RuntimeError("PEER_AGENTS is not set — add e.g. PEER_AGENTS=Agent-2=http://localhost:8001 to .env")

PRIMARY_PEER: str = next(iter(AGENT_REGISTRY))
