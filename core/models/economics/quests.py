from enum import Enum
from tortoise import fields
from tortoise.models import Model


class QuestType(str, Enum):
    SYSTEM = "system"
    PLAYER = "player"


class QuestStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Quest(Model):
    """
    Quest model for system and player quests

    - `id` (`BigInt`) - id of quest
    - `creator` (`models.Player`, optional) - creator (null for system quests)
    - `title` (`str`) - quest title
    - `description` (`str`) - quest description
    - `quest_type` (`ENUM.QuestType`) - SYSTEM or PLAYER
    - `reward_amount` (`int`) - reward in money
    - `payment_amount` (`int`) - payment for completion (for player quests)
    - `status` (`ENUM.QuestStatus`) - ACTIVE, COMPLETED, CANCELLED, EXPIRED
    - `max_completions` (`int`, optional) - maximum number of completions (null = unlimited)
    - `current_completions` (`int`) - current number of completions
    - `expires_at` (`Datetime`, optional) - expiration time
    - `requirements` (`dict`) - quest requirements (JSON)
    - `created_at` (`Datetime`) - creation time
    - `updated_at` (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    creator = fields.ForeignKeyField(
        "models.Player",
        related_name="quests_created",
        null=True,
        on_delete=fields.SET_NULL,
    )
    title = fields.CharField(max_length=128)
    description = fields.TextField()
    quest_type = fields.CharEnumField(QuestType, max_length=16)
    reward_amount = fields.IntField(default=0)
    payment_amount = fields.IntField(default=0)
    status = fields.CharEnumField(
        QuestStatus, max_length=16, default=QuestStatus.ACTIVE
    )
    max_completions = fields.IntField(null=True)
    current_completions = fields.IntField(default=0)
    expires_at = fields.DatetimeField(null=True)
    requirements = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "quests"
        indexes = ("quest_type", "status", "expires_at", "creator")


class QuestProgress(Model):
    """
    Quest progress model

    - `id` (`BigInt`) - id of quest progress
    - `quest` (`models.Quest`) - quest instance
    - `player` (`models.Player`) - player instance
    - `progress` (`dict`) - current progress (JSON)
    - `is_completed` (`bool`) - is quest completed
    - `completed_at` (`Datetime`, optional) - completion time
    - `claimed_reward` (`bool`) - is reward claimed
    - `created_at` (`Datetime`) - start time
    - `updated_at` (`Datetime`) - last update time
    """

    id = fields.BigIntField(pk=True)
    quest = fields.ForeignKeyField("models.Quest", related_name="progresses")
    player = fields.ForeignKeyField("models.Player", related_name="quest_progresses")
    progress = fields.JSONField(default=dict)
    is_completed = fields.BooleanField(default=False)
    completed_at = fields.DatetimeField(null=True)
    claimed_reward = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "quest_progress"
        unique_together = ("quest", "player")
        indexes = ("quest", "player", "is_completed")
