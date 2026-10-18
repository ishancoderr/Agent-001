"""The accounts that may log in, and the check of a password against them.

Accounts live in config/users.yaml (git-ignored; see config/users.example.yaml),
one entry per username with a display name and a bcrypt hash — never the
password itself:

    users:
      ishan:
        name: Ishan Weerakoon
        password_hash: $2b$12$...

The file is re-read when it changes, so `python -m agent1.auth add-user`
takes effect without restarting the agent.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

import bcrypt
import yaml

from ..settings import AUTH, CONFIG_DIR

USERS_PATH = Path(os.getenv("USERS_FILE") or CONFIG_DIR / AUTH["users_file"])

# Checked when a username is unknown, so a wrong username takes as long as a
# wrong password and the response time doesn't reveal which accounts exist.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())

_cache: Dict[str, Any] = {"mtime": None, "users": {}}
_lock = threading.Lock()


def load_users() -> Dict[str, Dict[str, str]]:
    """{username: {"name", "password_hash"}} from the users file ({} if it doesn't exist)."""
    with _lock:
        mtime = USERS_PATH.stat().st_mtime if USERS_PATH.exists() else None
        if mtime != _cache["mtime"]:
            data = yaml.safe_load(USERS_PATH.read_text(encoding="utf-8")) if mtime else None
            _cache.update(mtime=mtime, users=(data or {}).get("users") or {})
        return dict(_cache["users"])


def save_users(users: Dict[str, Dict[str, str]]) -> None:
    USERS_PATH.write_text(
        "# Accounts for the GeoQuery workbench — bcrypt hashes, never passwords.\n"
        "# Manage with: python -m agent1.auth add-user|remove-user|list-users\n"
        + yaml.safe_dump({"users": users}, sort_keys=True, allow_unicode=True),
        encoding="utf-8")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def check_password(username: str, password: str) -> Optional[Dict[str, str]]:
    """The account {"username", "name"} if the password is right, else None."""
    account = load_users().get(username)
    stored = account["password_hash"].encode("ascii") if account else _DUMMY_HASH
    ok = bcrypt.checkpw(password.encode("utf-8"), stored)
    if account and ok:
        return {"username": username, "name": account.get("name") or username}
    return None


class LoginGuard:
    """Locks a username for `lockout_minutes` after `max_failed_logins` wrong
    passwords in a row (settings.yaml auth). Kept in memory, per agent process."""

    def __init__(self, max_failures: int, lockout_s: float):
        self.max_failures, self.lockout_s = max_failures, lockout_s
        self._failures: Dict[str, int] = defaultdict(int)
        self._locked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def seconds_locked(self, username: str) -> float:
        with self._lock:
            return max(0.0, self._locked_until.get(username, 0.0) - time.monotonic())

    def failed(self, username: str) -> None:
        with self._lock:
            self._failures[username] += 1
            if self._failures[username] >= self.max_failures:
                self._locked_until[username] = time.monotonic() + self.lockout_s
                self._failures[username] = 0

    def succeeded(self, username: str) -> None:
        with self._lock:
            self._failures.pop(username, None)
            self._locked_until.pop(username, None)


GUARD = LoginGuard(int(AUTH["max_failed_logins"]), float(AUTH["lockout_minutes"]) * 60)
