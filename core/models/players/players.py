from enum import Enum
from tortoise import fields
from tortoise.models import Model
from core.models.localization.locale import Languages


class EraStamp(str, Enum):
    NEW_ERA = "new_era"
    WAR_ERA = "war_era"
    GOLDEN_ERA = "golden_era"
    SILENT_ERA = "silent_era"
    DARK_ERA = "dark_era"
    DEAD_ERA = "dead_era"


class PlayerRoles(str, Enum):
    GUEST = "guest"
    PLAYER = "player"
    MODERATOR = "moderator"
    SUPPORT = "support"
    ADMIN = "admin"
    OWNER = "owner"


class PlayerGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class PlayerSource(str, Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    TIKTOK = "tiktok"
    FRIEND = "friend"
    OTHER = "other"


class PlayerWorldRating(str, Enum):
    very_negative = "very_negative"
    negative = "negative"
    neutral = "neutral"
    positive = "positive"
    very_positive = "very_positive"


class Player(Model):
    """
    Base Player model
    - `id` (`BigInt`) - id of user into system
    - `tg_id` (`BigInt`) - id of user into telegram
    - `ds_id (`str`) - Discord user id (snowflake)
    - `role` (`ENUM.PlayerRoles`) - role on project
    - `balance` (`int`) - balance (vaysh) of player
    - `language` (`ENUM.Languages`) - player language
    - `ref_father` (`models.Player`) - referal father on project
    - `has_locked` (`bool`) - has locked bot (tg)?
    - `has_banned` (`bool`) - has banned on project?
    """

    id = fields.BigIntField(pk=True)
    tg_id = fields.BigIntField(unique=True, null=True)
    ds_id = fields.CharField(unique=True, null=True, max_length=32)
    nickname = fields.CharField(unique=True, null=True, max_length=32)

    role = fields.CharEnumField(PlayerRoles, default=PlayerRoles.GUEST)
    balance = fields.IntField(default=0)
    frozen_balance = fields.IntField(default=0)
    language = fields.CharEnumField(Languages, max_length=2, default=Languages.RU)

    ref_father = fields.ForeignKeyField(
        "models.Player",
        null=True,
        related_name="ref_children",
        on_delete=fields.SET_NULL,
    )
    has_locked = fields.BooleanField(default=False)  # locked bot?
    has_banned = fields.BooleanField(default=False)  # banned on project?

    class Meta:
        table = "player"


class PlayerProfile(Model):
    """
    Player profile model
    - `id` (`BigInt`) - id of player profile
    - `player` (`models.Player`) - player instance
    - `nickname` (`str`) - nickname of player on server
    - `age` (`int`) - age of player, >= 13
    - `gender` (`ENUM.Gender`) - gender of player
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player", related_name="profile", on_delete=fields.CASCADE
    )
    nickname = fields.CharField(max_length=32)
    age = fields.IntField(defaul=13)  # 13 - is minimum age
    gender = fields.CharEnumField(PlayerGender, max_length=8)
    source = fields.CharField(max_length=32)

    class Meta:
        table = "player_profile"


class PlayerAnalytics(Model):
    """
    Player analytics model
    - `id` (`BigInt`) - id of player analytics
    - `player` (`models.Player`) - player instance
    - `hours_played` (`int`) - hours played by player
    - `invites_count` (`int`) - invites count by player
    - `socials` (`list`) - list of socials (social_name: link)
    - `world_rating` (`ENUM.PlayerWorldRating`) - world rating of player
    - `clan_id` (`models.Clan`) - clan instance
    - `party_id` (`models.Party`) - party instance
    - `earned_money` (`int`) - earned money by player
    - `spent_money` (`int`) - spent money by player
    - `bio` (`str`) - bio of player
    - `era_stamp` (`ENUM.EraStamp`) - era stamp of player
    - `join_streak_days` (`int`) - join streak days of player
    - `join_streak_max` (`int`) - join streak max of player
    - `daily_streak_days` (`int`) - daily reward streak days of player
    - `daily_streak_max` (`int`) - max daily reward streak days of player
    - `last_daily_reward_at` (`Datetime`) - last time daily reward was claimed
    - `last_login` (`Datetime`) - last login of player
    - `in_war` (`bool`) - is player in war?
    """

    id = fields.BigIntField(pk=True)
    player = fields.ForeignKeyField(
        "models.Player", related_name="analytics", on_delete=fields.CASCADE
    )
    hours_played = fields.IntField(default=0)
    invites_count = fields.IntField(default=0)
    socials = fields.JSONField(default=list)  # {social_name: link}
    world_rating = fields.CharEnumField(
        PlayerWorldRating, max_length=16, default=PlayerWorldRating.neutral
    )

    clan_id = fields.ForeignKeyField(
        "models.Clan", related_name="clan", on_delete=fields.SET_NULL, null=True
    )
    party_id = fields.ForeignKeyField(
        "models.Party", related_name="party", on_delete=fields.SET_NULL, null=True
    )
    earned_money = fields.IntField(default=0)
    spent_money = fields.IntField(default=0)

    bio = fields.TextField(default="")
    era_stamp = fields.CharEnumField(EraStamp, max_length=16, default=EraStamp.NEW_ERA)

    join_streak_days = fields.IntField(default=0)
    join_streak_max = fields.IntField(default=0)
    daily_streak_days = fields.IntField(default=0)
    daily_streak_max = fields.IntField(default=0)
    last_daily_reward_at = fields.DatetimeField(null=True)

    last_login = fields.DatetimeField(null=True)
    in_war = fields.BooleanField(default=False)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "player_analytics"
