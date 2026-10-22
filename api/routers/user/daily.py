"""
User daily reward router.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_player
from api.schemas.economics import DailyRewardResponse
from core.managers.economics.transactions import grant_reward
from core.managers.players.profile import (
    create_player_analytics,
    get_player_analytics,
    update_player_analytics,
)
from core.models.players.players import Player
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "daily"])


async def process_daily_reward(player: Player) -> DailyRewardResponse:
    """
    Business logic for granting a daily reward to `player`.

    Raises HTTPException on cooldown violations and unexpected failures.
    """
    try:
        analytics = await get_player_analytics(player)
        if not analytics:
            analytics = await create_player_analytics(player)

        now = datetime.now(timezone.utc)
        last_daily = getattr(analytics, "last_daily_reward_at", None)
        streak_days = getattr(analytics, "daily_streak_days", 0) or 0
        streak_max = getattr(analytics, "daily_streak_max", 0) or 0

        if last_daily is not None:
            delta = now - last_daily
            if delta < timedelta(hours=24):
                next_available_at = last_daily + timedelta(hours=24)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Daily reward already claimed",
                        "next_available_at": next_available_at.isoformat(),
                    },
                )
            if delta < timedelta(hours=48):
                streak_days += 1
            else:
                streak_days = 1
        else:
            streak_days = 1

        if streak_days > streak_max:
            streak_max = streak_days

        import random

        base_amount = random.randint(50, 150)
        raw_multiplier = 1.0 + 0.1 * streak_days
        multiplier = min(raw_multiplier, 2.0)
        final_amount = int(base_amount * multiplier)

        await update_player_analytics(
            analytics=analytics,
            daily_streak_days=streak_days,
            daily_streak_max=streak_max,
            last_daily_reward_at=now,
        )

        reward_result = await grant_reward(
            player=player,
            amount=final_amount,
            description=f"Daily reward (streak={streak_days})",
            related_entity_type="daily_reward",
        )

        return DailyRewardResponse(
            base_amount=base_amount,
            streak_days=streak_days,
            streak_max=streak_max,
            multiplier=multiplier,
            final_amount=final_amount,
            next_available_at=now + timedelta(hours=24),
            balance_after=reward_result["balance_after"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process daily reward via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily", response_model=DailyRewardResponse)
async def daily_reward_endpoint(player: Player = Depends(get_current_player)):
    """
    Получить ежедневную награду (daily) для текущего игрока.

    Правила серии:
    - daily можно получить не чаще чем раз в 24 часа;
    - если с прошлого daily прошло >=24ч и <48ч — серия увеличивается на 1;
    - если прошло >=48ч — серия сбрасывается на 1;
    - множитель награды: 1.0 + 0.1 * streak_days, но не более 2.0.
    """
    return await process_daily_reward(player)
