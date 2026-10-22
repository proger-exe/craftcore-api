"""
Bot settings (key-value) for admin-configurable texts and options.
Category: safety. One model per block.
"""

from tortoise import fields
from tortoise.models import Model


class BotSettings(Model):
    """
    Key-value store for bot settings (e.g. form_approval_message).
    """

    key = fields.CharField(pk=True, max_length=128)
    value = fields.TextField(default="")

    class Meta:
        table = "bot_settings"
