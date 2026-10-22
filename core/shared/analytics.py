"""
Analytics and statistics functions
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from tortoise.expressions import Q
from core.models.players.players import Player, PlayerRoles
from core.models.economics.quests import Quest, QuestProgress
from core.models.economics.transactions import Transaction, TransactionType
from core.models.social.clans import Clan
from core.models.social.party import Party
from core.models.social.friends import Friend, FriendStatus
from core.shared.logger import logger


async def get_player_statistics(player: Player) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a player

    Args:
        player: Player instance

    Returns:
        Dictionary with player statistics
    """
    try:
        # Get profile and analytics if they exist
        from core.models.players.players import PlayerProfile, PlayerAnalytics

        profile = await PlayerProfile.get_or_none(player=player)
        analytics = await PlayerAnalytics.get_or_none(player=player)

        # Transaction statistics
        transactions = (
            await Transaction.filter(
                Q(from_player_id=player.id) | Q(to_player_id=player.id)
            )
            .prefetch_related("from_player", "to_player")
            .all()
        )

        incoming = sum(
            t.amount
            for t in transactions
            if t.to_player and t.to_player.id == player.id
        )
        outgoing = sum(
            t.amount
            for t in transactions
            if t.from_player and t.from_player.id == player.id
        )

        # Quest statistics
        quest_progresses = await QuestProgress.filter(player=player).all()
        completed_quests = sum(1 for qp in quest_progresses if qp.is_completed)
        active_quests = sum(1 for qp in quest_progresses if not qp.is_completed)

        # Social statistics
        friends_count = await Friend.filter(
            player=player, status=FriendStatus.ACCEPTED
        ).count()

        clan = None
        if analytics:
            clan_id_val = getattr(analytics, "clan_id_id", None)
            if clan_id_val is not None:
                clan = await Clan.get_or_none(id=clan_id_val)

        party = None
        if analytics:
            party_id_val = getattr(analytics, "party_id_id", None)
            if party_id_val is not None:
                party = await Party.get_or_none(id=party_id_val)

        return {
            "player_id": player.id,
            "nickname": player.nickname,
            "role": player.role.value,
            "balance": player.balance,
            "language": player.language.value,
            "profile": (
                {
                    "gender": (
                        profile.gender.value if profile and profile.gender else None
                    ),
                    "source": profile.source if profile else None,
                }
                if profile
                else None
            ),
            "analytics": (
                {
                    "hours_played": analytics.hours_played if analytics else 0,
                    "invites_count": analytics.invites_count if analytics else 0,
                    "earned_money": analytics.earned_money if analytics else 0,
                    "spent_money": analytics.spent_money if analytics else 0,
                    "join_streak_days": analytics.join_streak_days if analytics else 0,
                    "join_streak_max": analytics.join_streak_max if analytics else 0,
                    "last_login": (
                        analytics.last_login.isoformat()
                        if analytics and analytics.last_login
                        else None
                    ),
                }
                if analytics
                else None
            ),
            "transactions": {
                "total": len(transactions),
                "incoming": incoming,
                "outgoing": outgoing,
                "net": incoming - outgoing,
            },
            "quests": {
                "total": len(quest_progresses),
                "completed": completed_quests,
                "active": active_quests,
            },
            "social": {
                "friends_count": friends_count,
                "clan": clan.name if clan else None,
                "party": party.name if party else None,
            },
        }
    except Exception as e:
        logger.error(
            "Failed to get player statistics", error=str(e), player_id=player.id
        )
        raise


async def get_server_statistics() -> Dict[str, Any]:
    """
    Get server-wide statistics

    Returns:
        Dictionary with server statistics
    """
    try:
        # Player statistics
        total_players = await Player.all().count()
        players_by_role = {}
        for role in PlayerRoles:
            count = await Player.filter(role=role).count()
            players_by_role[role.value] = count

        # Economic statistics
        total_transactions = await Transaction.all().count()
        total_balance = sum([p.balance for p in await Player.all()])

        # Quest statistics
        total_quests = await Quest.all().count()
        active_quests = await Quest.filter(status="active").count()
        total_quest_progresses = await QuestProgress.all().count()
        completed_quests = await QuestProgress.filter(is_completed=True).count()

        # Social statistics
        total_clans = await Clan.all().count()
        total_parties = await Party.all().count()
        total_friends = await Friend.filter(status=FriendStatus.ACCEPTED).count()

        return {
            "players": {
                "total": total_players,
                "by_role": players_by_role,
            },
            "economy": {
                "total_transactions": total_transactions,
                "total_balance": total_balance,
            },
            "quests": {
                "total": total_quests,
                "active": active_quests,
                "total_progresses": total_quest_progresses,
                "completed": completed_quests,
                "completion_rate": (
                    completed_quests / total_quest_progresses
                    if total_quest_progresses > 0
                    else 0
                ),
            },
            "social": {
                "total_clans": total_clans,
                "total_parties": total_parties,
                "total_friends": total_friends,
            },
        }
    except Exception as e:
        logger.error("Failed to get server statistics", error=str(e))
        raise


async def get_economy_statistics(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get economy statistics for a date range

    Args:
        start_date: Start date (optional, defaults to 30 days ago)
        end_date: End date (optional, defaults to now)

    Returns:
        Dictionary with economy statistics
    """
    try:
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        query = Transaction.filter(created_at__gte=start_date, created_at__lte=end_date)

        transactions = await query.all()

        by_type = {}
        for trans_type in TransactionType:
            count = sum(1 for t in transactions if t.transaction_type == trans_type)
            amount = sum(
                t.amount for t in transactions if t.transaction_type == trans_type
            )
            if count > 0:
                by_type[trans_type.value] = {"count": count, "total_amount": amount}

        total_amount = sum(t.amount for t in transactions)
        total_count = len(transactions)

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_transactions": total_count,
            "total_amount": total_amount,
            "by_type": by_type,
            "average_transaction": total_amount / total_count if total_count > 0 else 0,
        }
    except Exception as e:
        logger.error("Failed to get economy statistics", error=str(e))
        raise


async def get_quest_completion_rate(quest: Quest) -> float:
    """
    Get quest completion rate

    Args:
        quest: Quest instance

    Returns:
        Completion rate as float (0.0 to 1.0)
    """
    try:
        total_starts = await QuestProgress.filter(quest=quest).count()
        if total_starts == 0:
            return 0.0

        completed = await QuestProgress.filter(quest=quest, is_completed=True).count()
        return completed / total_starts
    except Exception as e:
        logger.error(
            "Failed to get quest completion rate", error=str(e), quest_id=quest.id
        )
        raise


async def get_top_players_by_online_time(limit: int = 10, offset: int = 0):
    """
    Get top players by hours_played (PlayerAnalytics). Returns list of dicts:
    player_id, nickname, total_online_time (seconds), rank (1-based).
    """
    try:
        from core.models.players.players import PlayerAnalytics

        analytics_list = (
            await PlayerAnalytics.all()
            .order_by("-hours_played")
            .offset(offset)
            .limit(limit)
            .prefetch_related("player")
        )
        out = []
        for rank, a in enumerate(analytics_list, start=offset + 1):
            hours = a.hours_played or 0
            nick = a.player.nickname if a.player else None
            out.append(
                {
                    "player_id": a.player_id,
                    "nickname": nick,
                    "total_online_time": hours * 3600,
                    "rank": rank,
                }
            )
        return out
    except Exception as e:
        logger.error("Failed to get top players by online time", error=str(e))
        raise
