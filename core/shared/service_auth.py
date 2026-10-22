"""
Service-level JWT auth.

X-Player-ID says *which player* a request acts on behalf of, but nothing today
proves *which backend service* (Telegram bot, Discord bot, admin panel, ...)
is actually making the call — anyone who knows a valid player id can send it.
This is especially bad for the bootstrapped system account (id 777000, see
core/models/startup_migrations.py): knowing that one magic number is enough
to act as the system.

This module issues short-lived JWTs to known services (registered via the
SERVICE_CREDENTIALS env var, see settings.py) and verifies them. It does not
replace X-Player-ID for normal players — see api/dependencies.py, where only
requests for the system account are required to also carry a valid service
token.
"""

from datetime import datetime, timedelta, timezone

import jwt

from settings import settings

SYSTEM_PLAYER_ID = 777000


def _require_configured_secret() -> str:
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT_SECRET is not set in .env — service tokens cannot be issued or verified"
        )
    return settings.JWT_SECRET


def create_service_token(client_id: str) -> str:
    """Issue a JWT identifying `client_id` as the calling service."""
    _require_configured_secret()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": client_id,
        "scope": "service",
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_SERVICE_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_service_token(token: str) -> str:
    """Decode and validate a service JWT, returning the authenticated client_id.

    Raises jwt.PyJWTError (or a subclass) if the token is missing, expired,
    signed with the wrong secret, or not a service-scoped token.
    """
    _require_configured_secret()
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("scope") != "service":
        raise jwt.InvalidTokenError("Not a service token")
    return payload["sub"]
