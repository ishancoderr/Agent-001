"""
Login for the workbench and the agent's API.

- POST /auth/login checks a username and password against config/users.yaml
  (bcrypt hashes) and sets a signed session cookie; /auth/logout clears it;
  /auth/me says who is logged in.
- /query and /llms need that session (require_user); /health stays open.
- /kqml/receive, used only by the peer agent, needs AGENT_SHARED_KEY in the
  X-Agent-Key header (require_agent_key) instead.

Settings: config/settings.yaml `auth`; secrets AUTH_SECRET and AGENT_SHARED_KEY
in .env (the same values in both agents). Accounts:
    python -m agent1.auth add-user <name>
"""
from .routes import router
from .session import AuthUser, acting_as, current_user, require_agent_key, require_user

__all__ = ["router", "AuthUser", "acting_as", "current_user", "require_agent_key", "require_user"]
