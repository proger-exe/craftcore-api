from .economics import router as economics_router
from .social import router as social_router
from .mailing import router as mailing_router
from .qol import router as qol_router
from .clans import router as clans_router
from .party import router as party_router
from .shops import router as shops_router
from .market import router as market_router
from .profile import router as profile_router
from .voting import router as voting_router
from .rankings import router as rankings_router
from .referrals import router as referrals_router
from .nickchange import router as nickchange_router
from .player_quests import router as player_quests_router
from .daily import router as daily_router

user_routers = [
    player_quests_router,
    daily_router,
    economics_router,
    social_router,
    mailing_router,
    qol_router,
    clans_router,
    party_router,
    shops_router,
    market_router,
    profile_router,
    voting_router,
    rankings_router,
    referrals_router,
    nickchange_router,
]
