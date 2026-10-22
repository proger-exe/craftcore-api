"""
Module of safety system managers
Objects:
- Moderation (deps: /core/models/safety/moderation.py)
- Settings (deps: /core/models/safety/settings.py)
"""

from .moderation import *
from .settings import (
    get_all_settings,
    get_setting,
    set_setting,
    set_settings,
)
from .analytics import (
    create_server_snapshot,
    list_server_snapshots,
    create_or_update_player_session,
    list_player_sessions,
)
from .nickchange import (
    create_nick_change_request,
    list_nick_change_requests,
    approve_nick_change_request,
    reject_nick_change_request,
    get_player_nick_history,
)
