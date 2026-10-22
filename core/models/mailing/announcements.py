from enum import Enum
from tortoise import fields
from tortoise.models import Model


class TargetAudience(str, Enum):
    ALL = "all"
    PLAYERS = "players"
    ADMINS = "admins"
    GUESTS = "guests"


class Announcement(Model):
    """
    Announcement model for server announcements

    - `id` (`BigInt`) - id of announcement
    - `title` (`str`) - announcement title
    - `content` (`str`) - announcement content
    - `author` (`models.Player`, optional) - author (null for system announcements)
    - `is_active` (`bool`) - is announcement active
    - `priority` (`int`) - display priority
    - `target_audience` (`ENUM.TargetAudience`) - target audience
    - `scheduled_at` (`Datetime`, optional) - scheduled publication time
    - `expires_at` (`Datetime`, optional) - expiration time
    - `created_at` (`Datetime`) - creation time
    - `updated_at` (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    title = fields.CharField(max_length=128)
    content = fields.TextField()
    author = fields.ForeignKeyField(
        "models.Player",
        related_name="announcements_created",
        null=True,
        on_delete=fields.SET_NULL,
    )
    is_active = fields.BooleanField(default=True)
    priority = fields.IntField(default=0)
    target_audience = fields.CharEnumField(
        TargetAudience, max_length=16, default=TargetAudience.ALL
    )
    scheduled_at = fields.DatetimeField(null=True)
    expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "announcements"
        indexes = (
            "is_active",
            "priority",
            "target_audience",
            "scheduled_at",
            "expires_at",
        )
