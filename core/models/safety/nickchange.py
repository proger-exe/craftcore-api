"""
Nick change requests: one table. Category: safety.
"""

from tortoise import fields
from tortoise.models import Model


class NickChangeRequest(Model):
    """Request to change nickname. status: pending, approved, rejected."""

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player",
        related_name="nick_change_requests",
        on_delete=fields.CASCADE,
    )
    new_nick = fields.CharField(max_length=32)
    status = fields.CharField(max_length=16, default="pending")
    created_at = fields.DatetimeField(auto_now_add=True)
    history = fields.JSONField(default=list)

    class Meta:
        table = "nick_change_requests"
