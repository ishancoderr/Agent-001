"""python -m evaluator   — start the evaluator (host/port: settings.yaml, or EVALUATOR_HOST / EVALUATOR_PORT)."""
import logging

import uvicorn

from agent1.evaluation.log_files import daily_file_handler

from .config import HOST, PORT

# To the console and to logs/evaluator.log (a file per day, deleted after
# config/settings.yaml logs.keep_days); uvicorn's own loggers go the same way.
_file = daily_file_handler("evaluator.log")
_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    handlers=[logging.StreamHandler(), _file])
uvicorn.run("evaluator.api:app", host=HOST, port=PORT, log_config=None)
