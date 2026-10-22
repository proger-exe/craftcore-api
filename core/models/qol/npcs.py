from tortoise import fields
from tortoise.models import Model


class NPC(Model):
    """
    NPC model

    - id (`BigInt`) - id of npc
    - name (`str`) - name of npc
    - description (`str`) - description of npc
    - locate (`list`) - locate of npc (dim, x, y, z)
    - dialog (`list`) - dialog of npc (message_id: message_text) (can be more 1 message_id)
    - skin (`str`) - skin of npc (skin_url)
    - created_at (`Datetime`) - creation time
    - updated_at (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    description = fields.TextField(default="")

    locate = fields.JSONField(default=list)  # [dim, x, y, z]
    dialog = fields.JSONField(default=list)  # {message_id: message_text}
    skin = fields.CharField(max_length=128)  # skin_url

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
