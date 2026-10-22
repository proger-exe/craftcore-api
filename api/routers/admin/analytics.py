"""
Admin analytics: server snapshots and player sessions.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from api.dependencies import get_current_admin
from api.schemas.analytics import (
    PlaytimeRewardBatch,
    PlaytimeRewardRecord,
)
from core.models.players.players import Player
from core.managers.players.players import get_player
from core.managers.safety.analytics import (
    create_server_snapshot,
    list_server_snapshots,
    create_or_update_player_session,
    list_player_sessions,
    push_playtime_rewards,
    pop_playtime_rewards,
)
from core.shared.logger import logger

router = APIRouter(prefix="/admin", tags=["admin", "analytics"])


@router.post("/analytics/server-snapshot")
async def create_server_snapshot_endpoint(
    online_count: int = 0,
    alive: int = Query(1, ge=0, le=1),
    admin: Player = Depends(get_current_admin),
):
    """Create a server snapshot. Admin only."""
    try:
        snap = await create_server_snapshot(
            online_count=online_count, alive=bool(alive)
        )
        return {
            "id": snap.id,
            "online_count": snap.online_count,
            "alive": snap.alive,
            "timestamp": snap.timestamp.isoformat() if snap.timestamp else None,
        }
    except Exception as e:
        logger.error("Failed to create server snapshot via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/server-snapshots")
async def list_server_snapshots_endpoint(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    admin: Player = Depends(get_current_admin),
):
    """List server snapshots with optional date filter."""
    try:
        snaps = await list_server_snapshots(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return [
            {
                "id": s.id,
                "online_count": s.online_count,
                "alive": s.alive,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in snaps
        ]
    except Exception as e:
        logger.error("Failed to list server snapshots via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/player/{player_id}/sessions")
async def list_player_sessions_endpoint(
    player_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    admin: Player = Depends(get_current_admin),
):
    """List sessions for a player."""
    try:
        player = await get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        sessions = await list_player_sessions(
            player_id=player_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return [
            {
                "id": s.id,
                "player_id": s.player_id,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration_seconds": s.duration_seconds,
            }
            for s in sessions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list player sessions via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/player/{player_id}/session")
async def create_player_session_endpoint(
    player_id: int,
    body: Optional[dict] = None,
    admin: Player = Depends(get_current_admin),
):
    """Create or record a player session (for metrics collector). Body: start_time, end_time, duration."""
    try:
        player = await get_player(player_id)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        b = body or {}
        start_time = b.get("start_time")
        end_time = b.get("end_time")
        duration = b.get("duration")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        sess = await create_or_update_player_session(
            player=player,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
        )
        return {
            "id": sess.id,
            "player_id": sess.player_id,
            "start_time": sess.start_time.isoformat() if sess.start_time else None,
            "end_time": sess.end_time.isoformat() if sess.end_time else None,
            "duration_seconds": sess.duration_seconds,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create player session via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playtime-rewards")
async def push_playtime_rewards_endpoint(
    batch: PlaytimeRewardBatch,
    admin: Player = Depends(get_current_admin),
):
    """Push players with >=2h playtime into reward queue."""
    try:
        entries = [
            {
                "player_id": entry.player_id,
                "playtime_seconds": entry.playtime_seconds,
            }
            for entry in batch.players
        ]
        inserted = await push_playtime_rewards(entries)
        return {"inserted": inserted}
    except Exception as e:
        logger.error("Failed to push playtime rewards via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playtime-rewards/pending", response_model=List[PlaytimeRewardRecord])
async def pop_playtime_rewards_endpoint(
    admin: Player = Depends(get_current_admin),
):
    """Fetch and delete all pending playtime reward records."""
    try:
        records = await pop_playtime_rewards()
        return [
            {
                "id": int(r.id),
                "player_id": int(r.player_id),
                "playtime_seconds": int(r.playtime_seconds),
                "created_at": r.created_at,
            }
            for r in records
        ]
    except Exception as e:
        logger.error("Failed to pop playtime rewards via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
