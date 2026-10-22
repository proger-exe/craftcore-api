"""
Module of social system
Objects:
- Clans (deps: /app/routers/clans.py, /bot/module/clans, /dis_bot/module/clans)
- Parties (deps: /app/routers/parties.py, /bot/module/parties, /dis_bot/module/parties)
- Friends (deps: /app/routers/friends.py, /bot/module/friends, /dis_bot/module/friends)
"""

from .clans import Clan, ClanRole
from .party import Party, PartyRole
from .friends import Friend, FriendStatus
from .referrals import Referral

models = [
    "core.models.social.clans",
    "core.models.social.party",
    "core.models.social.friends",
    "core.models.social.referrals",
]
