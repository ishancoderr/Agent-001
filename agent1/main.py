"""
Agent 1 – FastAPI entry point
  POST /query          ← user submits a natural-language query
  POST /kqml/receive   ← peer agents send KQML 'ask' messages here
  GET  /health         ← liveness probe
"""
from __future__ import annotations

import logging

from fastapi import FastAPI

from .controller import query_router, kqml_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(title="Agent 1 – Geospatial Missing Data", version="1.0.0")

app.include_router(query_router)
app.include_router(kqml_router)
