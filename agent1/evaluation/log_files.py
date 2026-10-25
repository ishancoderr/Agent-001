"""
Log files in their own folder, kept for a few days only (config/settings.yaml
`logs`): each file starts afresh every midnight, and files older than
`keep_days` are deleted by themselves — at the daily switch, when the agent
starts, and at most once an hour while it runs.

Used for evaluation_metrics.log (agent1/evaluation/metrics_logger.py) and the
evaluator's evaluator.log.
"""
from __future__ import annotations

import logging
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from ..settings import LOGS

LOG_DIR: Path = Path(__file__).resolve().parents[2] / LOGS["dir"]
KEEP_DAYS: float = float(LOGS["keep_days"])
_PURGE_EVERY_S = 3600


def purge(filename: str) -> None:
    """Delete this log's files (the current one and its dated copies) that
    were last written more than KEEP_DAYS ago."""
    cutoff = time.time() - KEEP_DAYS * 86400
    for f in LOG_DIR.glob(f"{filename}*"):
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
        except OSError:                 # open elsewhere or already gone: next time
            pass


class _DailyHandler(TimedRotatingFileHandler):
    def __init__(self, filename: str) -> None:
        self._name = filename
        self._last_purge = 0.0
        super().__init__(LOG_DIR / filename, when="midnight", backupCount=max(int(KEEP_DAYS), 1),
                         encoding="utf-8", delay=True)

    def doRollover(self) -> None:
        super().doRollover()
        purge(self._name)

    def emit(self, record: logging.LogRecord) -> None:
        if time.time() - self._last_purge > _PURGE_EVERY_S:
            self._last_purge = time.time()
            purge(self._name)
        super().emit(record)


def daily_file_handler(filename: str) -> logging.Handler:
    """A handler writing LOG_DIR/<filename>, renewed daily, kept KEEP_DAYS days."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    purge(filename)
    return _DailyHandler(filename)
