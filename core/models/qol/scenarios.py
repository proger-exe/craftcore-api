from enum import Enum
from tortoise import fields
from tortoise.models import Model


class ScenarioType(str, Enum):
    """
    Scenario type
    """

    FIRST_JOIN = "first_join"
    REGULAR = "regular"
    EVENT = "event"
    ONE_TIME = "one_time"
    OTHER = "other"


class Scenario(Model):
    """
    Scenario model
    - id (`BigInt`) - id of scenario
    - name (`str`) - name of scenario
    - description (`str`) - description of scenario
    - arguments (`dict`) - arguments of scenario (required: [argument_value, type], optional: [argument_value, type])
    - command_stack (`list`) - command stack of scenario (command_name: [args])
    - scenario_type (`ENUM.ScenarioType`) - scenario type
    - created_at (`Datetime`) - creation time
    - updated_at (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    description = fields.TextField(default="")
    arguments = fields.JSONField(
        default=dict
    )  # {reqiured: [argument_value, type], optional: [argument_value, type]}
    command_stack = fields.JSONField(default=list)  # [command_name: [args]]
    scenario_type = fields.CharEnumField(ScenarioType, max_length=16)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "scenarios"
