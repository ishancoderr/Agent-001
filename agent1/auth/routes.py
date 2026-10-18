"""POST /auth/login, POST /auth/logout, GET /auth/me."""
from __future__ import annotations

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from .session import AuthUser, clear_cookie, issue, require_user, set_cookie
from .users import GUARD, check_password

log = logging.getLogger("agent1.auth")
router = APIRouter(prefix="/auth", tags=["login"])


class LoginBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=200)


@router.post("/login")
def login(body: LoginBody, response: Response) -> AuthUser:
    """Check the password; on success set the session cookie and return the user."""
    username = body.username.strip()
    locked = GUARD.seconds_locked(username)
    if locked:
        log.warning("AUTH   │ login refused for %r — locked for %.0f s more", username, locked)
        raise HTTPException(status_code=429, detail=(
            f"Too many wrong passwords — try again in {math.ceil(locked / 60)} minute(s)"))
    account = check_password(username, body.password)
    if account is None:
        GUARD.failed(username)
        log.warning("AUTH   │ wrong username or password for %r", username)
        raise HTTPException(status_code=401, detail="Wrong username or password")
    GUARD.succeeded(username)
    user = issue(account["username"], account["name"])
    set_cookie(response, user)
    log.info("AUTH   │ %s logged in", user.username)
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    """End the session in this browser (works even when it has already expired)."""
    clear_cookie(response)
    return {"logged_out": True}


@router.get("/me")
def me(user: AuthUser = Depends(require_user)) -> AuthUser:
    """Who is logged in — the workbench calls this when it opens."""
    return user
