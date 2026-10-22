"""
Admin wallet: freeze/unfreeze player balance.
"""

from fastapi import APIRouter, Depends
from core.models.players.players import Player
from core.managers.players.players import (
    get_player,
    freeze_player_balance,
    unfreeze_player_balance,
    get_available_balance,
)
from api.schemas.admin import WalletFreezeRequest, WalletUnfreezeRequest
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_admin
from core.shared.errors import NotFoundError, InsufficientBalanceError, ValidationError

router = APIRouter(prefix="/admin", tags=["admin", "wallet"])


@router.post("/wallet/{player_id}/freeze", response_model=SuccessResponse)
async def freeze_wallet_endpoint(
    player_id: int,
    body: WalletFreezeRequest,
    admin: Player = Depends(get_current_admin),
):
    """Freeze part of player balance. Admin only."""
    player = await get_player(player_id)
    if not player:
        raise NotFoundError("Player not found")
    try:
        await freeze_player_balance(player, body.amount, reason=body.reason)
    except ValueError as e:
        if "Insufficient" in str(e):
            raise InsufficientBalanceError(str(e))
        raise ValidationError(str(e))
    return SuccessResponse(message="Balance frozen successfully")


@router.post("/wallet/{player_id}/unfreeze", response_model=SuccessResponse)
async def unfreeze_wallet_endpoint(
    player_id: int,
    body: WalletUnfreezeRequest,
    admin: Player = Depends(get_current_admin),
):
    """Unfreeze part of player balance. Admin only."""
    player = await get_player(player_id)
    if not player:
        raise NotFoundError("Player not found")
    try:
        await unfreeze_player_balance(player, body.amount)
    except ValueError as e:
        raise ValidationError(str(e))
    return SuccessResponse(message="Balance unfrozen successfully")
