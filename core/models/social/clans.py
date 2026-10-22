from enum import Enum
from tortoise import fields
from tortoise.models import Model


class ClanRole(str, Enum):
    LEADER = "leader"
    MODERATOR = "moderator"
    MEMBER = "member"


class Clan(Model):
    """
    Base class of clan
    - `id` (`BigInt`) - id of clan
    - `name` (`str`) - name of clan
    - `owner` (`models.Player`) - Relation to Player model (who owns clan?)
    - `members` (`list`) - list of members (player_id: [id, ClanRole])
    - `name` (`str`) - name of clan
    - `description` (`str`) - description of clan
    - `tag` (`str`) - tag of clan
    - `prefix` (`str`) - prefix of clan
    - `inventory` (`list`) - list of items: [{"item_id": str, "quantity": int, "item_nbt": str}].
      Empty item_nbt = no NBT; same item_id with different item_nbt = different slots.
    - `balance` (`int`) - balance of clan
    - `homes` (`list`) - list of homes (home_id: [id, name, [dim, x, y, z]])
    """

    id = fields.BigIntField(pk=True)

    owner_id = fields.ForeignKeyField("models.Player", related_name="leader")
    members = fields.JSONField(default=list)  # {player_id: [id, ClanRole]}
    name = fields.CharField(max_length=32)
    description = fields.TextField(default="")
    tag = fields.CharField(max_length=5)
    prefix = fields.TextField(default="")
    inventory = fields.JSONField(
        default=list
    )  # [{"item_id": str, "quantity": int, "item_nbt": str}]
    balance = fields.IntField(default=0)
    homes = fields.JSONField(default=list)  # {home_id: [id, name, [dim, x, y, z]]}

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "clans"
