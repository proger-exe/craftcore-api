"""
Server snapshots and player sessions (for metrics collector and admin).
"""

from datetime import datetime
from typing import List, Optional, Dict

from tortoise.transactions import in_transaction

from core.models.safety.analytics import (
    ServerSnapshot,
    PlayerSession,
    PlaytimeRewardQueue,
)
from core.models.players.players import Player
from core.shared.logger import logger


async def create_server_snapshot(
    online_count: int = 0,
    alive: bool = True,
) -> ServerSnapshot:
    try:
        snap = await ServerSnapshot.create(
            online_count=online_count,
            alive=alive,
        )
        return snap
    except Exception as e:
        logger.error("Failed to create server snapshot", error=str(e))
        raise


async def list_server_snapshots(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> List[ServerSnapshot]:
    qs = ServerSnapshot.all().order_by("-timestamp").limit(limit)
    if start_date:
        qs = qs.filter(timestamp__gte=start_date)
    if end_date:
        qs = qs.filter(timestamp__lte=end_date)
    return await qs


async def create_or_update_player_session(
    player: Player,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
) -> PlayerSession:
    try:
        if duration_seconds is not None and start_time and end_time:
            sess = await PlayerSession.create(
                player=player,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
            )
        else:
            sess = await PlayerSession.create(
                player=player,
                start_time=start_time or datetime.utcnow(),
                end_time=end_time,
                duration_seconds=duration_seconds or 0,
            )
        return sess
    except Exception as e:
        logger.error("Failed to create player session", error=str(e))
        raise


async def list_player_sessions(
    player_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
) -> List[PlayerSession]:
    qs = (
        PlayerSession.filter(player_id=player_id)
        .order_by("-start_time")
        .limit(limit)
        .prefetch_related("player")
    )
    if start_date:
        qs = qs.filter(start_time__gte=start_date)
    if end_date:
        qs = qs.filter(start_time__lte=end_date)
    return await qs


async def push_playtime_rewards(entries: List[Dict[str, int]]) -> int:
    """Bulk-insert playtime reward records. Returns count inserted."""
    if not entries:
        return 0

    objs = [
        PlaytimeRewardQueue(
            player_id=e["player_id"],
            playtime_seconds=e["playtime_seconds"],
        )
        for e in entries
    ]
    await PlaytimeRewardQueue.bulk_create(objs)
    return len(objs)


async def pop_playtime_rewards() -> List[PlaytimeRewardQueue]:
    """Fetch all pending records and delete them atomically."""
    async with in_transaction() as conn:
        records = (
            await PlaytimeRewardQueue.all()
            .using_db(conn)
            .select_for_update()
            .order_by("created_at")
        )
        if not records:
            return []

        ids = [r.id for r in records]
        await PlaytimeRewardQueue.filter(id__in=ids).using_db(conn).delete()
    return records
