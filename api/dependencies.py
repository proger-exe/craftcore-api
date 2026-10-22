"""
API dependencies for authentication and authorization
"""

from typing import Optional, Union
import jwt
from fastapi import HTTPException, Header, Depends
from core.models.players.players import Player, PlayerRoles
from core.managers.players.players import get_player
from core.shared.logger import logger
from core.shared.service_auth import SYSTEM_PLAYER_ID, verify_service_token


def _parse_player_id(value: Optional[Union[int, str]]) -> Optional[int]:
    """Parse X-Player-ID header: int or string (string avoids JS bigint precision loss)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _require_service_auth(authorization: Optional[str]) -> str:
    """System account (777000) can only be impersonated by a trusted backend
    service holding a valid service JWT — see core/shared/service_auth.py and
    POST /integrations/auth/token. Anyone else sending X-Player-ID: 777000 is
    rejected, closing the "everyone knows the magic id" hole.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401, detail="System account requires a valid service token"
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_service_token(token)
    except (jwt.PyJWTError, RuntimeError):
        raise HTTPException(status_code=401, detail="Invalid or expired service token")


async def get_current_player(
    x_player_id: Optional[Union[int, str]] = Header(None, alias="X-Player-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Player:
    """
    Get current player from header.

    X-Player-ID can be int or string (use string for big IDs to avoid JSON number precision loss).
    """
    pid = _parse_player_id(x_player_id)
    if pid is None or pid <= 0:
        raise HTTPException(status_code=401, detail="Player ID is required")

    if pid == SYSTEM_PLAYER_ID:
        _require_service_auth(authorization)

    player = await get_player(pid)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player


async def get_current_admin(
    player: Player = Depends(get_current_player),
) -> Player:
    """
    Get current admin player (must have ADMIN or OWNER role)

    Args:
        player: Current player from dependency

    Returns:
        Player instance with admin role

    Raises:
        HTTPException: If player is not admin
    """
    if player.role not in [PlayerRoles.ADMIN, PlayerRoles.OWNER]:
        raise HTTPException(status_code=403, detail="Admin access required")

    return player


_MODERATOR_ROLES = (PlayerRoles.ADMIN, PlayerRoles.OWNER, PlayerRoles.MODERATOR)
_SUPPORT_ROLES = (*_MODERATOR_ROLES, PlayerRoles.SUPPORT)


async def get_current_moderator(
    player: Player = Depends(get_current_player),
) -> Player:
    """
    Get current moderator (ADMIN, OWNER, or MODERATOR). For Identity, search, dossier.
    """
    if player.role not in _MODERATOR_ROLES:
        raise HTTPException(status_code=403, detail="Moderator access required")
    return player


async def get_current_support(
    player: Player = Depends(get_current_player),
) -> Player:
    """
    Get current support (ADMIN, OWNER, MODERATOR, or SUPPORT). For read-only dashboard.
    """
    if player.role not in _SUPPORT_ROLES:
        raise HTTPException(status_code=403, detail="Support access required")
    return player


def validate_pagination(page: int = 1, per_page: int = 20) -> dict:
    """
    Validate pagination parameters

    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)

    Returns:
        Dictionary with validated pagination params

    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=400, detail="Per page must be between 1 and 100"
        )

    return {"page": page, "per_page": per_page}
