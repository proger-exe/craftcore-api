"""
Referral: one table, code + owner, joins in JSON. Category: social.
"""

from tortoise import fields
from tortoise.models import Model


class Referral(Model):
    """Referral code owned by a player; joins stored in JSON."""

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player",
        related_name="referral_codes",
        on_delete=fields.CASCADE,
    )
    code = fields.CharField(unique=True, max_length=32)
    joins = fields.JSONField(
        default=list
    )  # [{"player_id": int, "joined_at": "ISO8601"}]

    class Meta:
        table = "referrals"
