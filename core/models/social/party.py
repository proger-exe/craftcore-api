from enum import Enum
from tortoise import fields
from tortoise.models import Model


class PartyRole(str, Enum):
    LEADER = "leader"
    MEMBER = "member"


class Party(Model):
    """
    Base class of party
    - `id` (`BigInt`) - id of party
    - `name` (`str`) - name of party
    - `leader` (`models.Player`) - leader of party
    - `members` (`list`) - list of members ([ids])
    - `leader` (`models.Player`) - leader of party
    - `inventory` (`list`) - list of items (item_id: [id, quantity])
    """

    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    leader_id = fields.ForeignKeyField("models.Player", related_name="party_leader")
    members = fields.JSONField(default=list)  # [ids]
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "parties"
