"""
Voting manager: create vote, list, cast vote (with 1h playtime check), stats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from tortoise.transactions import in_transaction

from core.models.mailing.voting import Vote
from core.models.players.players import Player, PlayerAnalytics
from core.shared.logger import logger

MIN_PLAYTIME_HOURS_FOR_VOTE = 1


async def _player_playtime_seconds(player: Player) -> int:
    """Return player total playtime in seconds (hours_played * 3600)."""
    analytics = await PlayerAnalytics.get_or_none(player=player)
    if not analytics:
        return 0
    return (analytics.hours_played or 0) * 3600


def _recompute_option_counts(vote: Vote) -> None:
    """Update option 'votes' counts from votes list. Mutates vote.options in place."""
    votes_list = vote.votes or []
    counts: Dict[int, int] = {}
    for r in votes_list:
        oid = (
            r.get("option_id") if isinstance(r, dict) else getattr(r, "option_id", None)
        )
        if oid is not None:
            counts[oid] = counts.get(oid, 0) + 1
    options = list(vote.options or [])
    for i, opt in enumerate(options):
        o = dict(opt) if isinstance(opt, dict) else {}
        oid = o.get("id")
        o["votes"] = counts.get(oid, 0)
        options[i] = o
    vote.options = options


async def create_vote(
    created_by: Optional[Player],
    title: str,
    description: str = "",
    options: Optional[List[Dict[str, Any]]] = None,
    ends_at: Optional[datetime] = None,
) -> Vote:
    """Create a new vote. options: [{"id": 1, "text": "A"}, ...]."""
    try:
        opts = []
        for i, o in enumerate(options or []):
            if isinstance(o, dict):
                opts.append(
                    {
                        "id": o.get("id", i + 1),
                        "text": o.get("text", str(o)),
                        "votes": 0,
                    }
                )
            else:
                opts.append({"id": i + 1, "text": str(o), "votes": 0})
        for i, o in enumerate(opts):
            if o.get("id") is None:
                o["id"] = i + 1
        vote = await Vote.create(
            created_by=created_by,
            title=title,
            description=description,
            options=opts,
            votes=[],
            ends_at=ends_at,
        )
        logger.info("Vote created", vote_id=vote.id, title=title)
        return vote
    except Exception as e:
        logger.error("Failed to create vote", error=str(e))
        raise


async def get_vote(vote_id: int) -> Optional[Vote]:
    return await Vote.get_or_none(id=vote_id)


async def list_votes_active(limit: int = 50) -> List[Vote]:
    """List votes that are still active (ends_at is null or in future)."""
    from tortoise.expressions import Q

    now = datetime.utcnow()
    return (
        await Vote.filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
        .order_by("-created_at")
        .limit(limit)
    )


async def cast_vote(vote: Vote, player: Player, option_id: int) -> Vote:
    """
    Record a vote. Raises ValueError if already voted, option invalid, or playtime < 1h.
    """
    playtime = await _player_playtime_seconds(player)
    if playtime < MIN_PLAYTIME_HOURS_FOR_VOTE * 3600:
        raise ValueError("Need at least 1 hour playtime to vote")

    async with in_transaction() as conn:
        locked_vote = (
            await Vote.filter(id=vote.id).using_db(conn).select_for_update().first()
        )
        if not locked_vote:
            raise ValueError("Vote not found")

        votes_list = list(locked_vote.votes or [])
        for r in votes_list:
            pid = (
                r.get("player_id")
                if isinstance(r, dict)
                else getattr(r, "player_id", None)
            )
            if pid == player.id:
                raise ValueError("Already voted")

        option_ids = {
            o.get("id") if isinstance(o, dict) else getattr(o, "id", None)
            for o in (locked_vote.options or [])
        }
        if option_id not in option_ids:
            raise ValueError("Invalid option_id")

        votes_list.append({"player_id": player.id, "option_id": option_id})
        locked_vote.votes = votes_list
        _recompute_option_counts(locked_vote)
        await locked_vote.save(update_fields=["votes", "options"], using_db=conn)

    logger.info(
        "Vote cast", vote_id=locked_vote.id, player_id=player.id, option_id=option_id
    )
    return locked_vote


def get_vote_stats(vote: Vote) -> Dict[str, Any]:
    """Return options with votes and percentages."""
    _recompute_option_counts(vote)
    total = sum(o.get("votes", 0) for o in (vote.options or []))
    options_out = []
    for o in vote.options or []:
        v = o.get("votes", 0)
        pct = round(100.0 * v / total, 1) if total else 0
        options_out.append(
            {
                "id": o.get("id"),
                "text": o.get("text", ""),
                "votes": v,
                "percentage": pct,
            }
        )
    return {"total_votes": total, "options": options_out}
