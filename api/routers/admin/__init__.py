from .safety import router as safety_router
from .management import router as management_router
from .identity import router as identity_router
from .settings import router as settings_router
from .voting import router as admin_voting_router
from .wallet import router as wallet_router
from .analytics import router as analytics_router
from .referrals import router as referrals_admin_router
from .nickchange import router as nickchange_admin_router
from .qol import router as qol_admin_router

admin_routers = [
    safety_router,
    management_router,
    identity_router,
    settings_router,
    admin_voting_router,
    wallet_router,
    analytics_router,
    referrals_admin_router,
    nickchange_admin_router,
    qol_admin_router,
]
