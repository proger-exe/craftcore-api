"""
Admin identity router: lookup TG <-> Minecraft nick (/gettg, /getnick).
"""

from fastapi import APIRouter, HTTPException, Depends
from core.models.players.players import Player
from core.managers.players.players import (
    get_player_by_nickname,
    get_player_by_tg_id,
    unlink_telegram,
)
from api.schemas.identity import IdentityResponse
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_moderator
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "identity"])


def _player_to_identity_response(player: Player) -> IdentityResponse:
    verified = bool(player.tg_id is not None and player.nickname is not None)
    return IdentityResponse(
        player_id=player.id,
        tg_id=player.tg_id,
        nick=player.nickname,
        verified=verified,
    )


@router.get("/identity/nick/{nick}", response_model=IdentityResponse)
async def get_identity_by_nick_endpoint(
    nick: str, admin: Player = Depends(get_current_moderator)
):
    """Get tg_id and verified status by Minecraft nickname."""
    try:
        player = await get_player_by_nickname(nick)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return _player_to_identity_response(player)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get identity by nick via API", error=str(e), nick=nick)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/identity/telegram/{tg_id}", response_model=IdentityResponse)
async def get_identity_by_telegram_id_endpoint(
    tg_id: int, admin: Player = Depends(get_current_moderator)
):
    """Get nick and verified status by Telegram user id."""
    try:
        player = await get_player_by_tg_id(tg_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        return _player_to_identity_response(player)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get identity by tg_id via API", error=str(e), tg_id=tg_id
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/identity/telegram/username/{username}")
async def get_identity_by_telegram_username_endpoint(
    username: str, admin: Player = Depends(get_current_moderator)
):
    """Get nick by Telegram @username. Not implemented: no tg_username in Player yet."""
    raise HTTPException(
        status_code=501,
        detail="Lookup by Telegram username not implemented; Player has no tg_username field",
    )


@router.post("/identity/nick/{nick}/unlink-telegram", response_model=SuccessResponse)
async def unlink_telegram_from_nick_endpoint(
    nick: str, admin: Player = Depends(get_current_moderator)
):
    """Unlink Telegram account from player by Minecraft nickname."""
    try:
        player = await get_player_by_nickname(nick)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        if player.tg_id is None:
            raise HTTPException(
                status_code=400, detail="Player does not have Telegram linked"
            )

        await unlink_telegram(player)
        logger.info(
            "Telegram unlinked from player",
            player_id=player.id,
            nickname=nick,
            admin_id=admin.id,
        )
        return SuccessResponse(message="Telegram unlinked successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to unlink Telegram via API", error=str(e), nickname=nick
        )
        raise HTTPException(status_code=500, detail=str(e))
