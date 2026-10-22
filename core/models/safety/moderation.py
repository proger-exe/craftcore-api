from tortoise import fields
from tortoise.models import Model


class Ban(Model):
    """
    Ban model for player bans

    - `id` (`BigInt`) - id of ban
    - `player` (`models.Player`) - banned player
    - `admin` (`models.Player`, optional) - admin who banned (null for system bans)
    - `reason` (`str`) - ban reason
    - `banned_at` (`Datetime`) - ban time
    - `expires_at` (`Datetime`, optional) - expiration time (null = permanent)
    - `is_active` (`bool`) - is ban active
    - `unbanned_at` (`Datetime`, optional) - unban time
    - `unbanned_by` (`models.Player`, optional) - admin who unbanned
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField("models.Player", related_name="bans")
    admin = fields.ForeignKeyField(
        "models.Player", related_name="bans_given", null=True, on_delete=fields.SET_NULL
    )
    reason = fields.TextField()
    banned_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField(null=True)
    is_active = fields.BooleanField(default=True)
    unbanned_at = fields.DatetimeField(null=True)
    unbanned_by = fields.ForeignKeyField(
        "models.Player",
        related_name="unbans_given",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "bans"
        indexes = ("player", "is_active", "expires_at")


class Mute(Model):
    """
    Mute model for chat mutes

    - `id` (`BigInt`) - id of mute
    - `player` (`models.Player`) - muted player
    - `admin` (`models.Player`, optional) - admin who muted (null for system mutes)
    - `reason` (`str`) - mute reason
    - `muted_at` (`Datetime`) - mute time
    - `expires_at` (`Datetime`) - expiration time (required)
    - `is_active` (`bool`) - is mute active
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField("models.Player", related_name="mutes")
    admin = fields.ForeignKeyField(
        "models.Player",
        related_name="mutes_given",
        null=True,
        on_delete=fields.SET_NULL,
    )
    reason = fields.TextField()
    muted_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "mutes"
        indexes = ("player", "is_active", "expires_at")


class Warn(Model):
    """
    Warn model for player warnings

    - `id` (`BigInt`) - id of warn
    - `player` (`models.Player`) - warned player
    - `admin` (`models.Player`) - admin who warned
    - `reason` (`str`) - warn reason
    - `warned_at` (`Datetime`) - warn time
    - `is_active` (`bool`) - is warn active
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField("models.Player", related_name="warns")
    admin = fields.ForeignKeyField(
        "models.Player",
        related_name="warns_given",
        on_delete=fields.SET_NULL,
        null=True,
    )
    reason = fields.TextField()
    warned_at = fields.DatetimeField(auto_now_add=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "warns"
        indexes = ("player", "is_active")


class Arrest(Model):
    """
    Arrest model for player arrests

    - `id` (`BigInt`) - id of arrest
    - `player` (`models.Player`) - arrested player
    - `admin` (`models.Player`, optional) - admin who arrested (null for system arrests)
    - `reason` (`str`) - arrest reason
    - `arrested_at` (`Datetime`) - arrest time
    - `expires_at` (`Datetime`) - expiration time (required)
    - `is_active` (`bool`) - is arrest active
    - `released_at` (`Datetime`, optional) - early release time
    - `released_by` (`models.Player`, optional) - admin who released
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField("models.Player", related_name="arrests")
    admin = fields.ForeignKeyField(
        "models.Player",
        related_name="arrests_given",
        null=True,
        on_delete=fields.SET_NULL,
    )
    reason = fields.TextField()
    arrested_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()
    is_active = fields.BooleanField(default=True)
    released_at = fields.DatetimeField(null=True)
    released_by = fields.ForeignKeyField(
        "models.Player",
        related_name="releases_given",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "arrests"
        indexes = ("player", "is_active", "expires_at")


class AdminActionLog(Model):
    """
    Admin action log model

    - `id` (`BigInt`) - id of log entry
    - `admin` (`models.Player`) - admin who performed action
    - `action_type` (`str`) - type of action (ban, mute, warn, kick, etc.)
    - `target_player` (`models.Player`, optional) - target player
    - `details` (`dict`) - action details (JSON)
    - `created_at` (`Datetime`) - action time
    """

    id = fields.BigIntField(pk=True)
    admin = fields.ForeignKeyField("models.Player", related_name="admin_actions")
    action_type = fields.CharField(max_length=32)
    target_player = fields.ForeignKeyField(
        "models.Player",
        related_name="admin_actions_received",
        null=True,
        on_delete=fields.SET_NULL,
    )
    details = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "admin_action_logs"
        indexes = ("admin", "action_type", "created_at")
