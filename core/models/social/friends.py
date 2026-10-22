from enum import Enum
from tortoise import fields
from tortoise.models import Model


class FriendStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"


class Friend(Model):
    """
    Friend model for player friendships

    - `id` (`BigInt`) - id of friend relationship
    - `player` (`models.Player`) - player
    - `friend` (`models.Player`) - friend player
    - `status` (`ENUM.FriendStatus`) - PENDING, ACCEPTED, BLOCKED
    - `requested_at` (`Datetime`) - request time
    - `accepted_at` (`Datetime`, optional) - acceptance time
    - `created_at` (`Datetime`) - creation time
    - `updated_at` (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField("models.Player", related_name="friends")
    friend = fields.ForeignKeyField("models.Player", related_name="friends_reverse")
    status = fields.CharEnumField(
        FriendStatus, max_length=16, default=FriendStatus.PENDING
    )
    requested_at = fields.DatetimeField(auto_now_add=True)
    accepted_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "friends"
        unique_together = ("player", "friend")
        indexes = ("player", "friend", "status")
