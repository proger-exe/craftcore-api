"""
Module of mailing system
Objects:
- Announcements, Notifications, Voting (Vote)
"""

from .announcements import Announcement, TargetAudience
from .notifications import Notification, NotificationType
from .voting import Vote

models = [
    "core.models.mailing.announcements",
    "core.models.mailing.notifications",
    "core.models.mailing.voting",
]
