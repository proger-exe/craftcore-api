"""
User profile router
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.profile import (
    PlayerProfileResponse,
    PlayerProfileCreate,
    PlayerProfileUpdate,
    PlayerAnalyticsResponse,
    PlayerAnalyticsUpdate,
    SocialLinkAdd,
    TelegramLinkRequest,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player
from core.models.players.players import Player, PlayerGender, PlayerSource, PlayerRoles
from core.models.localization.locale import Languages
from core.managers.players.players import (
    create_player,
    get_player,
    get_player_by_tg_id,
    get_player_by_ds_id,
    get_player_by_nickname,
    link_telegram,
)
from core.managers.players.profile import (
    get_player_profile,
    create_player_profile,
    update_player_profile,
    get_player_analytics,
    create_player_analytics,
    update_player_analytics,
    add_social_link,
    remove_social_link,
    update_last_login,
)
from core.managers.safety.analytics import list_player_sessions
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "profile"])


def _analytics_to_response(analytics) -> PlayerAnalyticsResponse:
    """Собрать ответ. Перед вызовом должен быть выполнен fetch_related('player', 'clan_id', 'party_id')."""
    socials = analytics.socials if isinstance(analytics.socials, dict) else {}
    return PlayerAnalyticsResponse(
        id=analytics.id,
        player_id=analytics.player.id,
        hours_played=analytics.hours_played,
        invites_count=analytics.invites_count,
        socials=socials,
        world_rating=getattr(analytics.world_rating, "value", analytics.world_rating),
        clan_id=analytics.clan_id.id if analytics.clan_id else None,
        party_id=analytics.party_id.id if analytics.party_id else None,
        earned_money=analytics.earned_money,
        spent_money=analytics.spent_money,
        bio=analytics.bio,
        era_stamp=getattr(analytics.era_stamp, "value", analytics.era_stamp),
        join_streak_days=analytics.join_streak_days,
        join_streak_max=analytics.join_streak_max,
        last_login=analytics.last_login,
        in_war=analytics.in_war,
    )


@router.get("/profile/by-nickname/{nickname}", response_model=PlayerProfileResponse)
async def get_profile_by_nickname_endpoint(nickname: str):
    """
    Get player profile by nickname (no authentication required).

    If player exists but has no profile, a profile (and analytics) is created so
    the endpoint returns 200 instead of 404. Useful when the player was created
    elsewhere but profile was never created.
    """
    try:
        player = await get_player_by_nickname(nickname)
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")

        profile = await get_player_profile(player)
        if not profile:
            # Player exists but no profile — create so GET by nickname finds them
            analytics = await get_player_analytics(player)
            if not analytics:
                await create_player_analytics(player)
            profile = await create_player_profile(
                player=player,
                nickname=player.nickname or nickname.strip(),
                age=13,
                gender=PlayerGender.OTHER,
                source=PlayerSource.OTHER.value,
            )
            logger.info(
                "Profile auto-created for existing player (GET by nickname)",
                player_id=player.id,
                nickname=player.nickname,
            )

        await profile.fetch_related("player")
        return PlayerProfileResponse(
            id=profile.id,
            player_id=str(player.id),
            nickname=profile.nickname,
            age=profile.age,
            gender=profile.gender.value,
            source=profile.source,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get profile by nickname via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=PlayerProfileResponse)
async def get_profile_endpoint(player: Player = Depends(get_current_player)):
    """Get player profile"""
    try:
        profile = await get_player_profile(player)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        # Ensure player is loaded
        await profile.fetch_related("player")
        # Need to explicitly set player_id from profile.player.id
        return PlayerProfileResponse(
            id=profile.id,
            player_id=str(profile.player.id),
            nickname=profile.nickname,
            age=profile.age,
            gender=profile.gender.value,
            source=profile.source,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get profile via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile", response_model=PlayerProfileResponse, status_code=201)
async def create_profile_endpoint(profile_data: PlayerProfileCreate):
    """
    Create or get player profile (idempotent)

    System automatically creates a Player with auto-generated ID if player doesn't exist.
    This endpoint does not require authentication via X-Player-ID header
    because it's used for initial profile creation.

    Client MUST use the returned player_id in the X-Player-ID header for all subsequent
    requests (e.g. GET /user/profile, POST /user/shops). Without it, 404 Player not found.

    Logic:
    1. Check if player exists by tg_id, ds_id, or nickname (in that order)
    2. If player exists:
       - If profile exists, return existing profile (idempotent)
       - If profile doesn't exist, create profile for existing player
    3. If player doesn't exist, create new player and profile

    This endpoint is idempotent - calling it multiple times with same data will return same result.
    """
    _profile_log = logging.getLogger("api.profile")
    _profile_log.info(
        "POST /user/profile handler entered nickname=%s tg_id=%s ds_id=%s",
        profile_data.nickname,
        profile_data.tg_id,
        profile_data.ds_id,
    )
    try:
        player = None

        # Step 1: Check if player exists by tg_id, ds_id, or nickname (in that order)
        if profile_data.tg_id:
            player = await get_player_by_tg_id(profile_data.tg_id)
        elif profile_data.ds_id:
            player = await get_player_by_ds_id(profile_data.ds_id)

        # If not found by tg_id/ds_id, check by nickname
        if not player and profile_data.nickname:
            player = await get_player_by_nickname(profile_data.nickname)

        # Step 2: If player exists, check if profile exists
        if player:
            existing_profile = await get_player_profile(player)
            if existing_profile:
                # Profile already exists - ensure analytics exists (idempotent)
                analytics = await get_player_analytics(player)
                if not analytics:
                    await create_player_analytics(player)
                await existing_profile.fetch_related("player")
                return PlayerProfileResponse(
                    id=existing_profile.id,
                    player_id=str(player.id),
                    nickname=existing_profile.nickname,
                    age=existing_profile.age,
                    gender=existing_profile.gender.value,
                    source=existing_profile.source,
                )

            # Player exists but no profile - create profile for existing player
            # Update nickname if provided and different
            if profile_data.nickname and player.nickname != profile_data.nickname:
                player.nickname = profile_data.nickname
                await player.save()
        else:
            # Step 3: Player doesn't exist - create new player (by nickname only or with tg_id/ds_id)
            logger.info(
                "Creating new player",
                nickname=profile_data.nickname,
                by_nickname_only=not (profile_data.tg_id or profile_data.ds_id),
            )
            player = await create_player(
                tg_id=profile_data.tg_id,
                ds_id=profile_data.ds_id,
                nickname=profile_data.nickname,
                role=PlayerRoles.GUEST,
                balance=0,
                language=Languages.RU,
            )
            # CRITICAL: After create, ALWAYS reload from DB to get the actual ID.
            # Tortoise/DB may not populate ID on the same object; reload by unique field or by id.
            reloaded_player = None
            if profile_data.tg_id:
                reloaded_player = await get_player_by_tg_id(profile_data.tg_id)
            elif profile_data.ds_id:
                reloaded_player = await get_player_by_ds_id(profile_data.ds_id)
            elif profile_data.nickname:
                reloaded_player = await get_player_by_nickname(profile_data.nickname)

            if reloaded_player and (reloaded_player.id or 0) > 0:
                player = reloaded_player
                logger.info(
                    "Player reloaded after creation",
                    player_id=str(player.id),
                    nickname=profile_data.nickname,
                )
            else:
                await player.refresh_from_db()
                logger.info(
                    "Player refreshed from DB after creation",
                    player_id=str(player.id),
                    nickname=profile_data.nickname,
                )

            # Final check: never return 201 with invalid player_id (client must use this id in X-Player-ID)
            if not player.id or player.id <= 0:
                logger.error(
                    "Player created but ID is not available after reload",
                    nickname=profile_data.nickname,
                    tg_id=profile_data.tg_id,
                    ds_id=profile_data.ds_id,
                    player_id_from_object=player.id,
                )
                raise HTTPException(
                    status_code=500, detail="Failed to create player: ID not assigned"
                )

        # Create profile (either for existing player or newly created)
        source_value = profile_data.source or PlayerSource.OTHER.value
        profile = await create_player_profile(
            player=player,
            nickname=profile_data.nickname,
            age=profile_data.age or 13,
            gender=profile_data.gender or PlayerGender.OTHER,
            source=source_value,
        )

        # При создании профиля всегда проверяем наличие аналитики и создаём при отсутствии
        analytics = await get_player_analytics(player)
        if not analytics:
            await create_player_analytics(player)

        # Ensure profile is saved and ID is available
        if not profile.id:
            await profile.refresh_from_db()

        # Log for debugging
        logger.info(
            "Profile created/retrieved",
            profile_id=profile.id,
            player_id=str(player.id),
            nickname=profile_data.nickname,
        )

        # Verify player_id is valid before returning (client MUST use this in X-Player-ID)
        if not player.id or player.id <= 0:
            logger.error(
                "Invalid player_id in response",
                player_id=str(player.id),
                nickname=profile_data.nickname,
            )
            raise HTTPException(
                status_code=500, detail=f"Invalid player_id: {player.id}"
            )

        # Re-fetch player by id so response always reflects DB state
        player_for_response = await get_player(player.id)
        if not player_for_response:
            logger.error(
                "Player not found by id after profile creation",
                player_id=str(player.id),
                nickname=profile_data.nickname,
            )
            raise HTTPException(
                status_code=500, detail="Player not found after creation"
            )

        return PlayerProfileResponse(
            id=profile.id,
            player_id=str(player_for_response.id),
            nickname=profile.nickname,
            age=profile.age,
            gender=profile.gender.value,
            source=profile.source,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create profile via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile", response_model=PlayerProfileResponse)
async def update_profile_endpoint(
    profile_data: PlayerProfileUpdate, player: Player = Depends(get_current_player)
):
    """Update player profile"""
    try:
        profile = await get_player_profile(player)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        updated = await update_player_profile(
            profile=profile,
            nickname=profile_data.nickname,
            age=profile_data.age,
            gender=profile_data.gender,
            source=profile_data.source,
        )
        # Ensure player is loaded
        await updated.fetch_related("player")
        # Need to explicitly set player_id from updated.player.id
        return PlayerProfileResponse(
            id=updated.id,
            player_id=str(updated.player.id),
            nickname=updated.nickname,
            age=updated.age,
            gender=updated.gender.value,
            source=updated.source,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update profile via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_my_sessions_endpoint(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    player: Player = Depends(get_current_player),
):
    """Get current player's play sessions (no admin required)."""
    try:
        sessions = await list_player_sessions(
            player_id=player.id,
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
    except Exception as e:
        logger.error("Failed to get sessions via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=PlayerAnalyticsResponse)
async def get_analytics_endpoint(player: Player = Depends(get_current_player)):
    """Get player analytics (создаёт запись при отсутствии)"""
    try:
        analytics = await get_player_analytics(player)
        if not analytics:
            analytics = await create_player_analytics(player)
        await analytics.fetch_related("player", "clan_id", "party_id")
        return _analytics_to_response(analytics)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get analytics via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/analytics", response_model=PlayerAnalyticsResponse)
async def update_analytics_endpoint(
    analytics_data: PlayerAnalyticsUpdate,
    player: Player = Depends(get_current_player),
):
    """Update player analytics"""
    try:
        analytics = await get_player_analytics(player)
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")

        updated = await update_player_analytics(
            analytics=analytics,
            bio=analytics_data.bio,
            world_rating=analytics_data.world_rating,
            era_stamp=analytics_data.era_stamp,
            last_login=analytics_data.last_login,
            join_streak_days=analytics_data.join_streak_days,
            join_streak_max=analytics_data.join_streak_max,
        )
        await updated.fetch_related("player", "clan_id", "party_id")
        return _analytics_to_response(updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update analytics via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/socials", response_model=SuccessResponse)
async def add_social_link_endpoint(
    social_data: SocialLinkAdd, player: Player = Depends(get_current_player)
):
    """Add social link to player analytics"""
    try:
        analytics = await get_player_analytics(player)
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")

        await add_social_link(
            analytics=analytics,
            social_name=social_data.social_name,
            link=social_data.link,
        )
        return SuccessResponse(message="Social link added successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add social link via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analytics/socials/{social_name}", response_model=SuccessResponse)
async def remove_social_link_endpoint(
    social_name: str, player: Player = Depends(get_current_player)
):
    """Remove social link from player analytics"""
    try:
        analytics = await get_player_analytics(player)
        if not analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")

        await remove_social_link(analytics=analytics, social_name=social_name)
        return SuccessResponse(message="Social link removed successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove social link via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/telegram/link", response_model=SuccessResponse)
async def link_telegram_endpoint(
    body: TelegramLinkRequest, player: Player = Depends(get_current_player)
):
    """Link Telegram account to the current player. Fails if tg_id is already linked to another account."""
    try:
        await link_telegram(player=player, tg_id=body.tg_id)
        return SuccessResponse(message="Telegram linked successfully")
    except ValueError as e:
        if "already linked" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to link Telegram via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
