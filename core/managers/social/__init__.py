"""
Module of social system managers
Objects:
- Clans (deps: /core/models/social/clans.py)
- Parties (deps: /core/models/social/party.py)
- Friends (deps: /core/models/social/friends.py)
"""

from .clans import *
from .party import *
from .friends import *
from .referrals import (
    get_or_create_referral_code,
    join_referral,
    get_referral_stats,
    get_all_referral_stats,
)
