from tortoise import fields
from tortoise.models import Model


class Craft(Model):
    """
    Craft model
    - id (`BigInt`) - id of craft
    - icon (`str`) - icon of craft (icon_url)
    - name (`str`) - name of craft
    - description (`str`) - description of craft
    - recipe (`list`) - recipe of craft (item_id: [id, quantity])
    - created_at (`Datetime`) - creation time
    - updated_at (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    icon = fields.CharField(max_length=128)
    name = fields.CharField(max_length=32)
    description = fields.TextField(default="")
    recipe = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "crafts"
