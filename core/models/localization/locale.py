from tortoise import fields
from tortoise.models import Model
from enum import Enum


class Languages(str, Enum):
    RU = "ru"
    EN = "en"


class Message(Model):
    """
    Message model for storing localized text messages

    - `message_id` (`str`): Unique identifier for the message (max 4028 chars)
    - `message_name` (`str`, optional): Human-readable name/description of the message
    - `message_text` (`str`): Primary language text of the message
    - `message_text_another_langs` (`dict`): JSON field containing translations
        Example: {"en": "Hello!", "ru": "Привет!", ...}
        Uses language code as key for getting alternative language text
    """

    message_id = fields.CharField(max_length=128, unique=True)
    message_name = fields.TextField(null=True)

    message_text = fields.TextField()
    message_text_another_langs = fields.JSONField(default={})

    class Meta:
        table = "message"


class Button(Model):
    """
    Button model for storing localized button texts

    - `button_id` (`str`): Identifier for the button (max 128 chars).
        Multiple buttons can share the same button_id for different languages
    - `button_text` (`str`): Text displayed on the button
    - `lang` (`Languages`): Language code for this button text (enum: RU or EN)
    """

    button_id = fields.CharField(max_length=128, unique=True)
    button_text = fields.TextField()
    lang = fields.CharEnumField(Languages)

    class Meta:
        table = "button"
