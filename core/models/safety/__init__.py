"""
Module of safety system
Objects:
- Moderation: Ban, Mute, Warn, AdminActionLog
- BotSettings, ServerSnapshot, PlayerSession (analytics)
"""

from .moderation import Ban, Mute, Warn, AdminActionLog
from .settings import BotSettings
from .analytics import ServerSnapshot, PlayerSession
from .nickchange import NickChangeRequest

models = [
    "core.models.safety.moderation",
    "core.models.safety.settings",
    "core.models.safety.analytics",
    "core.models.safety.nickchange",
]
