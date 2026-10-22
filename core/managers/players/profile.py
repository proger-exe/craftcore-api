"""
Player profile and analytics manager for CRUD operations
"""

from typing import Optional, Dict, List
from datetime import datetime
from core.models.players.players import (
    Player,
    PlayerProfile,
    PlayerAnalytics,
    PlayerGender,
    PlayerSource,
    EraStamp,
    PlayerWorldRating,
)
from core.models.social.clans import Clan
from core.models.social.party import Party
from core.shared.logger import logger

# Чтобы не сбрасывать clan_id/party_id при обновлении только одного из них
_UNCHANGED = object()


# PlayerProfile CRUD operations


async def create_player_profile(
    player: Player,
    nickname: str,
    age: int = 13,
    gender: PlayerGender = PlayerGender.OTHER,
    source: str = PlayerSource.OTHER.value,
) -> PlayerProfile:
    """
    Create a new player profile

    Args:
        player: Player instance
        nickname: Nickname on server (max 32 chars)
        age: Age of player (default: 13, minimum)
        gender: Gender of player (default: OTHER)
        source: Source of player registration (default: OTHER)

    Returns:
        PlayerProfile: Created profile instance

    Raises:
        ValueError: If age is less than 13
        Exception: If creation fails
    """
    if age < 13:
        raise ValueError("Age must be >= 13")

    try:
        profile = await PlayerProfile.create(
            player=player,
            nickname=nickname,
            age=age,
            gender=gender,
            source=source,
        )
        logger.info(
            "👤 Player profile created", profile_id=profile.id, player_id=player.id
        )
        return profile
    except Exception as e:
        logger.error(
            "Failed to create player profile", error=str(e), player_id=player.id
        )
        raise


async def get_player_profile(player: Player) -> Optional[PlayerProfile]:
    """
    Get player profile by player (lookup by player_id to avoid any FK resolution issues).

    Args:
        player: Player instance

    Returns:
        PlayerProfile or None if not found
    """
    try:
        return await PlayerProfile.get_or_none(player_id=player.id)
    except Exception as e:
        logger.error("Failed to get player profile", error=str(e), player_id=player.id)
        raise


async def update_player_profile(
    profile: PlayerProfile,
    nickname: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[PlayerGender] = None,
    source: Optional[str] = None,
) -> PlayerProfile:
    """
    Update player profile fields

    Args:
        profile: PlayerProfile instance to update
        nickname: New nickname (optional)
        age: New age (optional, must be >= 13)
        gender: New gender (optional)
        source: New source (optional)

    Returns:
        Updated PlayerProfile instance

    Raises:
        ValueError: If age is less than 13
        Exception: If update fails
    """
    try:
        if nickname is not None:
            profile.nickname = nickname
        if age is not None:
            if age < 13:
                raise ValueError("Age must be >= 13")
            profile.age = age
        if gender is not None:
            profile.gender = gender
        if source is not None:
            profile.source = source

        await profile.save()
        logger.info("🔄 Player profile updated", profile_id=profile.id)
        return profile
    except Exception as e:
        logger.error(
            "Failed to update player profile", error=str(e), profile_id=profile.id
        )
        raise


async def delete_player_profile(profile: PlayerProfile) -> None:
    """
    Delete player profile (cascades from player deletion)

    Args:
        profile: PlayerProfile instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        profile_id = profile.id
        await profile.delete()
        logger.info("🗑️ Player profile deleted", profile_id=profile_id)
    except Exception as e:
        logger.error(
            "Failed to delete player profile", error=str(e), profile_id=profile_id
        )
        raise


# PlayerAnalytics CRUD operations


async def create_player_analytics(
    player: Player,
    world_rating: PlayerWorldRating = PlayerWorldRating.neutral,
    era_stamp: EraStamp = EraStamp.NEW_ERA,
) -> PlayerAnalytics:
    """
    Create a new player analytics record

    Args:
        player: Player instance
        world_rating: World rating of player (default: neutral)
        era_stamp: Era stamp of player (default: NEW_ERA)

    Returns:
        PlayerAnalytics: Created analytics instance

    Raises:
        Exception: If creation fails
    """
    try:
        analytics = await PlayerAnalytics.create(
            player=player,
            hours_played=0,
            invites_count=0,
            socials=[],
            world_rating=world_rating,
            earned_money=0,
            spent_money=0,
            bio="",
            era_stamp=era_stamp,
            join_streak_days=0,
            join_streak_max=0,
            daily_streak_days=0,
            daily_streak_max=0,
            last_daily_reward_at=None,
            in_war=False,
        )
        logger.info(
            "📊 Player analytics created",
            analytics_id=analytics.id,
            player_id=player.id,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to create player analytics", error=str(e), player_id=player.id
        )
        raise


async def get_player_analytics(player: Player) -> Optional[PlayerAnalytics]:
    """
    Get player analytics by player

    Args:
        player: Player instance

    Returns:
        PlayerAnalytics or None if not found
    """
    try:
        return await PlayerAnalytics.get_or_none(player=player)
    except Exception as e:
        logger.error(
            "Failed to get player analytics", error=str(e), player_id=player.id
        )
        raise


async def update_player_analytics(
    analytics: PlayerAnalytics,
    hours_played: Optional[int] = None,
    invites_count: Optional[int] = None,
    socials: Optional[List[Dict[str, str]]] = None,
    world_rating: Optional[PlayerWorldRating] = None,
    clan_id: Optional[Clan] = _UNCHANGED,
    party_id: Optional[Party] = _UNCHANGED,
    earned_money: Optional[int] = None,
    spent_money: Optional[int] = None,
    bio: Optional[str] = None,
    era_stamp: Optional[EraStamp] = None,
    join_streak_days: Optional[int] = None,
    join_streak_max: Optional[int] = None,
    daily_streak_days: Optional[int] = None,
    daily_streak_max: Optional[int] = None,
    last_daily_reward_at: Optional[datetime] = None,
    last_login: Optional[datetime] = None,
    in_war: Optional[bool] = None,
) -> PlayerAnalytics:
    """
    Update player analytics fields

    Args:
        analytics: PlayerAnalytics instance to update
        hours_played: New hours played (optional)
        invites_count: New invites count (optional)
        socials: New socials list (optional)
        world_rating: New world rating (optional)
        clan_id: New clan (optional, None to clear; не передавать = не менять)
        party_id: New party (optional, None to clear; не передавать = не менять)
        earned_money: New earned money (optional)
        spent_money: New spent money (optional)
        bio: New bio (optional)
        era_stamp: New era stamp (optional)
        join_streak_days: New join streak days (optional)
        join_streak_max: New join streak max (optional)
        daily_streak_days: New daily reward streak days (optional)
        daily_streak_max: New max daily reward streak days (optional)
        last_daily_reward_at: New datetime of last daily reward claim (optional)
        last_login: New last login datetime (optional)
        in_war: New in_war status (optional)

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If any numeric value is negative
        Exception: If update fails
    """
    try:
        if hours_played is not None:
            if hours_played < 0:
                raise ValueError("Hours played must be >= 0")
            analytics.hours_played = hours_played
        if invites_count is not None:
            if invites_count < 0:
                raise ValueError("Invites count must be >= 0")
            analytics.invites_count = invites_count
        if socials is not None:
            analytics.socials = socials
        if world_rating is not None:
            analytics.world_rating = world_rating
        if clan_id is not _UNCHANGED:
            analytics.clan_id = clan_id
        if party_id is not _UNCHANGED:
            analytics.party_id = party_id
        if earned_money is not None:
            if earned_money < 0:
                raise ValueError("Earned money must be >= 0")
            analytics.earned_money = earned_money
        if spent_money is not None:
            if spent_money < 0:
                raise ValueError("Spent money must be >= 0")
            analytics.spent_money = spent_money
        if bio is not None:
            analytics.bio = bio
        if era_stamp is not None:
            analytics.era_stamp = era_stamp
        if join_streak_days is not None:
            if join_streak_days < 0:
                raise ValueError("Join streak days must be >= 0")
            analytics.join_streak_days = join_streak_days
        if join_streak_max is not None:
            if join_streak_max < 0:
                raise ValueError("Join streak max must be >= 0")
            analytics.join_streak_max = join_streak_max
        if daily_streak_days is not None:
            if daily_streak_days < 0:
                raise ValueError("Daily streak days must be >= 0")
            analytics.daily_streak_days = daily_streak_days
        if daily_streak_max is not None:
            if daily_streak_max < 0:
                raise ValueError("Daily streak max must be >= 0")
            analytics.daily_streak_max = daily_streak_max
        if last_daily_reward_at is not None:
            analytics.last_daily_reward_at = last_daily_reward_at
        if last_login is not None:
            analytics.last_login = last_login
        if in_war is not None:
            analytics.in_war = in_war

        await analytics.save()
        logger.info("🔄 Player analytics updated", analytics_id=analytics.id)
        return analytics
    except Exception as e:
        logger.error(
            "Failed to update player analytics", error=str(e), analytics_id=analytics.id
        )
        raise


async def increase_hours_played(
    analytics: PlayerAnalytics, hours: int
) -> PlayerAnalytics:
    """
    Increase hours played

    Args:
        analytics: PlayerAnalytics instance
        hours: Hours to add

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If hours is negative
        Exception: If update fails
    """
    if hours < 0:
        raise ValueError("Hours must be >= 0")

    try:
        analytics.hours_played += hours
        await analytics.save()
        logger.info(
            "⏱️ Hours played increased",
            analytics_id=analytics.id,
            hours=hours,
            total_hours=analytics.hours_played,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to increase hours played",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def increase_invites_count(
    analytics: PlayerAnalytics, count: int = 1
) -> PlayerAnalytics:
    """
    Increase invites count

    Args:
        analytics: PlayerAnalytics instance
        count: Count to add (default: 1)

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If count is negative
        Exception: If update fails
    """
    if count < 0:
        raise ValueError("Count must be >= 0")

    try:
        analytics.invites_count += count
        await analytics.save()
        logger.info(
            "📈 Invites count increased",
            analytics_id=analytics.id,
            count=count,
            total_invites=analytics.invites_count,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to increase invites count",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def add_social_link(
    analytics: PlayerAnalytics, social_name: str, link: str
) -> PlayerAnalytics:
    """
    Add or update social link

    Args:
        analytics: PlayerAnalytics instance
        social_name: Name of social network
        link: Link to social profile

    Returns:
        Updated PlayerAnalytics instance
    """
    try:
        socials = analytics.socials or []
        # Check if social already exists and update, otherwise add
        found = False
        for i, social in enumerate(socials):
            if isinstance(social, dict) and social.get("name") == social_name:
                socials[i] = {"name": social_name, "link": link}
                found = True
                break

        if not found:
            socials.append({"name": social_name, "link": link})

        analytics.socials = socials
        await analytics.save()
        logger.info(
            "🔗 Social link added",
            analytics_id=analytics.id,
            social_name=social_name,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to add social link",
            error=str(e),
            analytics_id=analytics.id,
            social_name=social_name,
        )
        raise


async def remove_social_link(
    analytics: PlayerAnalytics, social_name: str
) -> PlayerAnalytics:
    """
    Remove social link

    Args:
        analytics: PlayerAnalytics instance
        social_name: Name of social network to remove

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If social link not found
    """
    try:
        socials = analytics.socials or []
        original_length = len(socials)

        analytics.socials = [
            social
            for social in socials
            if not (isinstance(social, dict) and social.get("name") == social_name)
        ]

        if len(analytics.socials) == original_length:
            raise ValueError("Social link not found")

        await analytics.save()
        logger.info(
            "🗑️ Social link removed",
            analytics_id=analytics.id,
            social_name=social_name,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to remove social link",
            error=str(e),
            analytics_id=analytics.id,
            social_name=social_name,
        )
        raise


async def increase_earned_money(
    analytics: PlayerAnalytics, amount: int
) -> PlayerAnalytics:
    """
    Increase earned money

    Args:
        analytics: PlayerAnalytics instance
        amount: Amount to add

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If amount is negative
        Exception: If update fails
    """
    if amount < 0:
        raise ValueError("Amount must be >= 0")

    try:
        analytics.earned_money += amount
        await analytics.save()
        logger.info(
            "💰 Earned money increased",
            analytics_id=analytics.id,
            amount=amount,
            total_earned=analytics.earned_money,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to increase earned money",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def increase_spent_money(
    analytics: PlayerAnalytics, amount: int
) -> PlayerAnalytics:
    """
    Increase spent money

    Args:
        analytics: PlayerAnalytics instance
        amount: Amount to add

    Returns:
        Updated PlayerAnalytics instance

    Raises:
        ValueError: If amount is negative
        Exception: If update fails
    """
    if amount < 0:
        raise ValueError("Amount must be >= 0")

    try:
        analytics.spent_money += amount
        await analytics.save()
        logger.info(
            "💸 Spent money increased",
            analytics_id=analytics.id,
            amount=amount,
            total_spent=analytics.spent_money,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to increase spent money",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def update_last_login(
    analytics: PlayerAnalytics, login_time: Optional[datetime] = None
) -> PlayerAnalytics:
    """
    Update last login time

    Args:
        analytics: PlayerAnalytics instance
        login_time: Login datetime (default: current time)

    Returns:
        Updated PlayerAnalytics instance
    """
    try:
        analytics.last_login = login_time or datetime.now()
        await analytics.save()
        logger.info("🕐 Last login updated", analytics_id=analytics.id)
        return analytics
    except Exception as e:
        logger.error(
            "Failed to update last login",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def increase_join_streak(analytics: PlayerAnalytics) -> PlayerAnalytics:
    """
    Increase join streak days and update max if needed

    Args:
        analytics: PlayerAnalytics instance

    Returns:
        Updated PlayerAnalytics instance
    """
    try:
        analytics.join_streak_days += 1
        if analytics.join_streak_days > analytics.join_streak_max:
            analytics.join_streak_max = analytics.join_streak_days
        await analytics.save()
        logger.info(
            "🔥 Join streak increased",
            analytics_id=analytics.id,
            streak_days=analytics.join_streak_days,
            max_streak=analytics.join_streak_max,
        )
        return analytics
    except Exception as e:
        logger.error(
            "Failed to increase join streak",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def reset_join_streak(analytics: PlayerAnalytics) -> PlayerAnalytics:
    """
    Reset join streak days to 0

    Args:
        analytics: PlayerAnalytics instance

    Returns:
        Updated PlayerAnalytics instance
    """
    try:
        analytics.join_streak_days = 0
        await analytics.save()
        logger.info("🔄 Join streak reset", analytics_id=analytics.id)
        return analytics
    except Exception as e:
        logger.error(
            "Failed to reset join streak",
            error=str(e),
            analytics_id=analytics.id,
        )
        raise


async def delete_player_analytics(analytics: PlayerAnalytics) -> None:
    """
    Delete player analytics (cascades from player deletion)

    Args:
        analytics: PlayerAnalytics instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        analytics_id = analytics.id
        await analytics.delete()
        logger.info("🗑️ Player analytics deleted", analytics_id=analytics_id)
    except Exception as e:
        logger.error(
            "Failed to delete player analytics", error=str(e), analytics_id=analytics_id
        )
        raise
