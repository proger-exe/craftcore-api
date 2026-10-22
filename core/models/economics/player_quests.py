"""Player-created marketplace tasks and applications."""

from tortoise import fields
from tortoise.models import Model


class PlayerQuest(Model):
    """Quest created by a player; reward is frozen until completion/cancel."""

    id = fields.BigIntField(pk=True)
    creator = fields.ForeignKeyField(
        "models.Player",
        related_name="player_quests_created",
        on_delete=fields.CASCADE,
    )
    title = fields.CharField(max_length=128)
    description = fields.TextField()
    reward = fields.IntField()
    status = fields.CharField(max_length=32, default="open")
    executor = fields.ForeignKeyField(
        "models.Player",
        related_name="player_quests_taken",
        null=True,
        on_delete=fields.SET_NULL,
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "player_quests"
        indexes = ("creator_id", "status", "executor_id", "created_at")


class PlayerQuestApplication(Model):
    """Application/submission workflow for a player quest."""

    id = fields.BigIntField(pk=True)
    quest = fields.ForeignKeyField(
        "models.PlayerQuest",
        related_name="applications",
        on_delete=fields.CASCADE,
    )
    applicant = fields.ForeignKeyField(
        "models.Player",
        related_name="player_quest_applications",
        on_delete=fields.CASCADE,
    )
    status = fields.CharField(max_length=32, default="applied")
    cover_letter = fields.TextField(null=True)
    submission_message = fields.TextField(null=True)
    review_comment = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "player_quest_applications"
        indexes = ("quest_id", "applicant_id", "status", "created_at")
