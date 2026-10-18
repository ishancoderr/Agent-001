"""python -m evaluator   — start the evaluator (host/port: settings.yaml, or EVALUATOR_HOST / EVALUATOR_PORT)."""
import logging

import uvicorn

from .config import HOST, PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
uvicorn.run("evaluator.api:app", host=HOST, port=PORT)
