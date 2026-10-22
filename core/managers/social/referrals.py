"""
Referral manager: get/create code, join by code, stats.
"""

import secrets
from datetime import datetime
from typing import Dict, Any, Optional

from core.models.social.referrals import Referral
from core.models.players.players import Player
from core.managers.players.players import update_player, get_player
from core.shared.db import locked_row
from core.shared.errors import ValidationError
from core.shared.logger import logger


def _generate_code() -> str:
    return secrets.token_hex(4).upper()[:8]


async def get_or_create_referral_code(player: Player) -> Referral:
    """Get existing referral for player or create one with a new code."""
    ref = await Referral.get_or_none(player=player)
    if ref:
        return ref
    for _ in range(5):
        code = _generate_code()
        if await Referral.get_or_none(code=code):
            continue
        ref = await Referral.create(player=player, code=code, joins=[])
        logger.info("Referral code created", player_id=player.id, code=code)
        return ref
    raise RuntimeError("Could not generate unique referral code")


async def join_referral(joiner: Player, code: str) -> None:
    """Register joiner as referred by code. Sets ref_father on joiner."""
    normalized_code = code.upper().strip()
    existing = await Referral.get_or_none(code=normalized_code)
    if not existing:
        raise ValidationError("Invalid referral code")

    async with locked_row(Referral, id=existing.id) as ref:
        if ref.player_id == joiner.id:
            raise ValidationError("Cannot use own referral code")
        joins = list(ref.joins or [])
        for j in joins:
            if isinstance(j, dict) and j.get("player_id") == joiner.id:
                raise ValidationError("Already joined with this code")
        joins.append(
            {
                "player_id": joiner.id,
                "joined_at": datetime.utcnow().isoformat() + "Z",
            }
        )
        ref.joins = joins
        await ref.save(update_fields=["joins"])
        await ref.fetch_related("player")
        referrer_player = ref.player

    await update_player(joiner, ref_father=referrer_player)
    logger.info(
        "Referral join", code=code, joiner_id=joiner.id, referrer_id=ref.player_id
    )


async def get_referral_stats(player: Player) -> Dict[str, Any]:
    """Stats for one player's referral code."""
    ref = await Referral.get_or_none(player=player)
    if not ref:
        ref = await get_or_create_referral_code(player)
    joins = ref.joins or []
    return {
        "code": ref.code,
        "total_referrals": len(joins),
        "qualified": len(joins),
        "rewards": [],
    }


async def get_all_referral_stats() -> Dict[str, Any]:
    """Admin: aggregate referral stats."""
    refs = await Referral.all().prefetch_related("player")
    total_joins = sum(len(r.joins or []) for r in refs)
    return {
        "total_codes": len(refs),
        "total_joins": total_joins,
    }
