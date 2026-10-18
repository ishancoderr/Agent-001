"""The signed session a login creates, and the checks every protected route uses.

A session is a JWT (HS256, signed with AUTH_SECRET from .env) holding the
username, display name and expiry, sent as an HttpOnly cookie — JavaScript
can't read it, the browser sends it only to this site (SameSite=Strict) and,
unless COOKIE_SECURE=false, only over HTTPS. Both agents share AUTH_SECRET, so
a login made through one is accepted by the other.

Agent-to-agent KQML doesn't use a session: it carries AGENT_SHARED_KEY in the
X-Agent-Key header (require_agent_key).
"""
from __future__ import annotations

import hmac
import logging
import os
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException, Request, Response
from pydantic import BaseModel

from ..settings import AUTH

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

log = logging.getLogger("agent1.auth")

_MIN_SECRET_LENGTH = 32


def _secret(name: str) -> str:
    """A required secret from .env; the agent refuses to start without it."""
    value = os.getenv(name, "")
    if len(value) < _MIN_SECRET_LENGTH:
        raise RuntimeError(
            f"{name} is missing or shorter than {_MIN_SECRET_LENGTH} characters — add a long random value "
            f"to this agent's .env (the same value in both agents), e.g. from:\n"
            f'  python -c "import secrets; print(secrets.token_urlsafe(48))"')
    return value


AUTH_SECRET = _secret("AUTH_SECRET")
AGENT_SHARED_KEY = _secret("AGENT_SHARED_KEY")
COOKIE_NAME: str = AUTH["cookie_name"]
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").strip().lower() != "false"
SESSION_SECONDS = int(float(AUTH["session_hours"]) * 3600)
_ISSUER = "geoquery-agents"


class AuthUser(BaseModel):
    username: str
    name: str
    expires_at: int            # unix time the session ends


def issue(username: str, name: str) -> AuthUser:
    now = int(time.time())
    return AuthUser(username=username, name=name, expires_at=now + SESSION_SECONDS)


def encode(user: AuthUser) -> str:
    claims = {"sub": user.username, "name": user.name, "iat": int(time.time()),
              "exp": user.expires_at, "iss": _ISSUER}
    return jwt.encode(claims, AUTH_SECRET, algorithm="HS256")


def decode(token: str) -> Optional[AuthUser]:
    """The user a token belongs to, or None if it is forged, expired or malformed."""
    try:
        claims = jwt.decode(token, AUTH_SECRET, algorithms=["HS256"], issuer=_ISSUER,
                            options={"require": ["sub", "exp", "iss"]})
    except jwt.PyJWTError:
        return None
    return AuthUser(username=claims["sub"], name=claims.get("name") or claims["sub"], expires_at=claims["exp"])


def set_cookie(response: Response, user: AuthUser) -> None:
    response.set_cookie(COOKIE_NAME, encode(user), max_age=SESSION_SECONDS, httponly=True,
                        secure=COOKIE_SECURE, samesite="strict", path="/")


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True, secure=COOKIE_SECURE, samesite="strict")


def require_user(request: Request) -> AuthUser:
    """Route dependency: the logged-in user, or 401."""
    user = decode(request.cookies.get(COOKIE_NAME, ""))
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in, or the session has ended — log in again")
    return user


def require_agent_key(x_agent_key: Optional[str] = Header(None)) -> None:
    """Route dependency for agent-to-agent KQML: the shared agent key, or 401."""
    if not x_agent_key or not hmac.compare_digest(x_agent_key, AGENT_SHARED_KEY):
        raise HTTPException(status_code=401, detail="Missing or wrong X-Agent-Key")


# The user a request is being answered for — for the logs and evaluation metrics.
_current: ContextVar[Optional[str]] = ContextVar("auth_user", default=None)


@contextmanager
def acting_as(user: AuthUser) -> Iterator[None]:
    token = _current.set(user.username)
    try:
        yield
    finally:
        _current.reset(token)


def current_user() -> Optional[str]:
    return _current.get()
