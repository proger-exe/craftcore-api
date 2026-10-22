"""
Server and player session analytics. Category: safety. Two models (server + sessions).
"""

from tortoise import fields
from tortoise.models import Model


class ServerSnapshot(Model):
    """One snapshot of server state: online count, alive, timestamp."""

    id = fields.BigIntField(pk=True)
    online_count = fields.IntField(default=0)
    alive = fields.BooleanField(default=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "server_snapshots"


class PlayerSession(Model):
    """One play session: player, start, end, duration (seconds)."""

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player",
        related_name="sessions",
        on_delete=fields.CASCADE,
    )
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField(null=True)
    duration_seconds = fields.IntField(default=0)

    class Meta:
        table = "player_sessions"


class PlaytimeRewardQueue(Model):
    """Queue of players who reached 2+ hours playtime. Consumed and deleted by the bot."""

    id = fields.BigIntField(pk=True)
    player_id = fields.BigIntField()
    playtime_seconds = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "playtime_reward_queue"
