from enum import Enum
from tortoise import fields
from tortoise.models import Model


class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Notification(Model):
    """
    Notification model for player notifications

    - `id` (`BigInt`) - id of notification
    - `player` (`models.Player`, optional) - recipient (null for bulk notifications)
    - `title` (`str`) - notification title
    - `content` (`str`) - notification content
    - `notification_type` (`ENUM.NotificationType`) - INFO, WARNING, ERROR, SUCCESS
    - `is_read` (`bool`) - is notification read
    - `read_at` (`Datetime`, optional) - read time
    - `created_at` (`Datetime`) - creation time
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player",
        related_name="notifications",
        null=True,
        on_delete=fields.CASCADE,
    )
    title = fields.CharField(max_length=128)
    content = fields.TextField()
    notification_type = fields.CharEnumField(
        NotificationType, max_length=16, default=NotificationType.INFO
    )
    is_read = fields.BooleanField(default=False)
    read_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"
        indexes = ("player", "is_read", "notification_type", "created_at")
