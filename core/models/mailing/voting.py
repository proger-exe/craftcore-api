"""
Vote model: single table with options and vote records in JSON.
Category: mailing. One model per block.
"""

from tortoise import fields
from tortoise.models import Model


class Vote(Model):
    """
    Poll/vote: title, description, options (JSON), vote records (JSON).
    options: [{"id": 1, "text": "Option A", "votes": 0}, ...]
    votes: [{"player_id": 123, "option_id": 1}, ...]
    """

    id = fields.BigIntField(pk=True)
    created_by = fields.ForeignKeyField(
        "models.Player",
        related_name="votes_created",
        null=True,
        on_delete=fields.SET_NULL,
    )
    title = fields.CharField(max_length=256)
    description = fields.TextField(default="")
    options = fields.JSONField(default=list)  # [{"id": int, "text": str, "votes": int}]
    votes = fields.JSONField(default=list)  # [{"player_id": int, "option_id": int}]
    created_at = fields.DatetimeField(auto_now_add=True)
    ends_at = fields.DatetimeField(null=True)

    class Meta:
        table = "votes"
