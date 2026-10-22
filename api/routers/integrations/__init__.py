from .tgbot import router as tgbot_router
from .auth import router as auth_router

integration_routers = [tgbot_router, auth_router]
