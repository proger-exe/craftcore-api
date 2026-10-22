"""
Export and import functions for data migration
"""

from typing import Dict, Any, Optional
from datetime import datetime
from core.models.players.players import (
    Player,
    PlayerProfile,
    PlayerAnalytics,
    PlayerRoles,
    PlayerGender,
    PlayerSource,
    Languages,
)
from core.models.economics.quests import Quest, QuestType, QuestStatus
from core.shared.logger import logger


async def export_player_data(player: Player) -> Dict[str, Any]:
    """
    Export all player data to dictionary

    Args:
        player: Player instance

    Returns:
        Dictionary with all player data
    """
    try:
        profile = await PlayerProfile.get_or_none(player=player)
        analytics = await PlayerAnalytics.get_or_none(player=player)

        data = {
            "player": {
                "id": player.id,
                "tg_id": player.tg_id,
                "ds_id": player.ds_id,
                "nickname": player.nickname,
                "role": player.role.value,
                "balance": player.balance,
                "language": player.language.value,
                "has_locked": player.has_locked,
                "has_banned": player.has_banned,
                "ref_father_id": player.ref_father.id if player.ref_father else None,
            },
        }

        if profile:
            data["profile"] = {
                "gender": profile.gender.value if profile.gender else None,
                "source": profile.source.value if profile.source else None,
            }

        if analytics:
            data["analytics"] = {
                "hours_played": analytics.hours_played,
                "invites_count": analytics.invites_count,
                "socials": analytics.socials,
                "world_rating": (
                    analytics.world_rating.value if analytics.world_rating else None
                ),
                "clan_id": analytics.clan_id.id if analytics.clan_id else None,
                "party_id": analytics.party_id.id if analytics.party_id else None,
                "earned_money": analytics.earned_money,
                "spent_money": analytics.spent_money,
                "bio": analytics.bio,
                "era_stamp": analytics.era_stamp.value if analytics.era_stamp else None,
                "join_streak_days": analytics.join_streak_days,
                "join_streak_max": analytics.join_streak_max,
                "last_login": (
                    analytics.last_login.isoformat() if analytics.last_login else None
                ),
                "in_war": analytics.in_war,
            }

        logger.info("📤 Player data exported", player_id=player.id)
        return data
    except Exception as e:
        logger.error("Failed to export player data", error=str(e), player_id=player.id)
        raise


async def import_player_data(data: Dict[str, Any]) -> Player:
    """
    Import player data from dictionary

    Args:
        data: Dictionary with player data

    Returns:
        Created or updated Player instance

    Raises:
        ValueError: If required data is missing
        Exception: If import fails
    """
    try:
        if "player" not in data:
            raise ValueError("Player data is required")

        player_data = data["player"]

        # Check if player exists
        player = None
        if "id" in player_data:
            player = await Player.get_or_none(id=player_data["id"])
        elif player_data.get("tg_id"):
            player = await Player.get_or_none(tg_id=player_data["tg_id"])
        elif player_data.get("ds_id"):
            player = await Player.get_or_none(ds_id=player_data["ds_id"])
        elif player_data.get("nickname"):
            player = await Player.get_or_none(nickname=player_data["nickname"])

        if player:
            # Update existing player
            if "balance" in player_data:
                player.balance = player_data["balance"]
            if "role" in player_data:
                player.role = PlayerRoles(player_data["role"])
            if "language" in player_data:
                player.language = Languages(player_data["language"])
            if "has_locked" in player_data:
                player.has_locked = player_data["has_locked"]
            if "has_banned" in player_data:
                player.has_banned = player_data["has_banned"]
            await player.save()
        else:
            # Create new player
            from core.managers.players.players import create_player

            player = await create_player(
                tg_id=player_data.get("tg_id"),
                ds_id=player_data.get("ds_id"),
                nickname=player_data.get("nickname"),
                role=PlayerRoles(player_data.get("role", "guest")),
                balance=player_data.get("balance", 0),
                language=Languages(player_data.get("language", "ru")),
            )

        # Import profile if exists
        if "profile" in data and data["profile"]:
            profile_data = data["profile"]
            profile = await PlayerProfile.get_or_none(player=player)
            if profile:
                from core.managers.players.profile import update_player_profile

                await update_player_profile(
                    profile,
                    gender=(
                        PlayerGender(profile_data["gender"])
                        if profile_data.get("gender")
                        else None
                    ),
                    source=(
                        PlayerSource(profile_data["source"])
                        if profile_data.get("source")
                        else None
                    ),
                )
            else:
                from core.managers.players.profile import create_player_profile

                await create_player_profile(
                    player,
                    gender=(
                        PlayerGender(profile_data["gender"])
                        if profile_data.get("gender")
                        else None
                    ),
                    source=(
                        PlayerSource(profile_data["source"])
                        if profile_data.get("source")
                        else None
                    ),
                )

        # Import analytics if exists
        if "analytics" in data and data["analytics"]:
            analytics_data = data["analytics"]
            analytics = await PlayerAnalytics.get_or_none(player=player)
            if analytics:
                from core.managers.players.profile import update_player_analytics

                await update_player_analytics(
                    analytics,
                    hours_played=analytics_data.get("hours_played"),
                    invites_count=analytics_data.get("invites_count"),
                    socials=analytics_data.get("socials"),
                    earned_money=analytics_data.get("earned_money"),
                    spent_money=analytics_data.get("spent_money"),
                    bio=analytics_data.get("bio"),
                    join_streak_days=analytics_data.get("join_streak_days"),
                    join_streak_max=analytics_data.get("join_streak_max"),
                    last_login=(
                        datetime.fromisoformat(analytics_data["last_login"])
                        if analytics_data.get("last_login")
                        else None
                    ),
                    in_war=analytics_data.get("in_war"),
                )
            else:
                from core.managers.players.profile import create_player_analytics

                await create_player_analytics(
                    player,
                    hours_played=analytics_data.get("hours_played", 0),
                    invites_count=analytics_data.get("invites_count", 0),
                    socials=analytics_data.get("socials", {}),
                    earned_money=analytics_data.get("earned_money", 0),
                    spent_money=analytics_data.get("spent_money", 0),
                    bio=analytics_data.get("bio"),
                    join_streak_days=analytics_data.get("join_streak_days", 0),
                    join_streak_max=analytics_data.get("join_streak_max", 0),
                    last_login=(
                        datetime.fromisoformat(analytics_data["last_login"])
                        if analytics_data.get("last_login")
                        else None
                    ),
                    in_war=analytics_data.get("in_war", False),
                )

        logger.info("📥 Player data imported", player_id=player.id)
        return player
    except Exception as e:
        logger.error("Failed to import player data", error=str(e))
        raise


async def export_quest_data(quest: Quest) -> Dict[str, Any]:
    """
    Export quest data to dictionary

    Args:
        quest: Quest instance

    Returns:
        Dictionary with quest data
    """
    try:
        data = {
            "id": quest.id,
            "creator_id": quest.creator.id if quest.creator else None,
            "title": quest.title,
            "description": quest.description,
            "quest_type": quest.quest_type.value,
            "reward_amount": quest.reward_amount,
            "payment_amount": quest.payment_amount,
            "status": quest.status.value,
            "max_completions": quest.max_completions,
            "current_completions": quest.current_completions,
            "expires_at": quest.expires_at.isoformat() if quest.expires_at else None,
            "requirements": quest.requirements,
            "created_at": quest.created_at.isoformat(),
            "updated_at": quest.updated_at.isoformat(),
        }

        logger.info("📤 Quest data exported", quest_id=quest.id)
        return data
    except Exception as e:
        logger.error("Failed to export quest data", error=str(e), quest_id=quest.id)
        raise
