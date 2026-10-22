from enum import Enum
from tortoise import fields
from tortoise.models import Model


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    TRANSFER = "transfer"
    REWARD = "reward"
    QUEST_PAYMENT = "quest_payment"
    REFUND = "refund"
    TAX = "tax"
    FINE = "fine"


class Transaction(Model):
    """
    Transaction model for all economic transactions

    - `id` (`BigInt`) - id of transaction
    - `from_player` (`models.Player`, optional) - sender (null for system transactions)
    - `to_player` (`models.Player`, optional) - receiver (null for system transactions)
    - `amount` (`int`) - transaction amount
    - `transaction_type` (`ENUM.TransactionType`) - type of transaction
    - `description` (`str`) - transaction description
    - `related_entity_type` (`str`, optional) - type of related entity (market_item, shop_item, quest, etc.)
    - `related_entity_id` (`BigInt`, optional) - ID of related entity
    - `created_at` (`Datetime`) - transaction time
    """

    id = fields.BigIntField(pk=True)
    from_player = fields.ForeignKeyField(
        "models.Player",
        related_name="transactions_sent",
        null=True,
        on_delete=fields.SET_NULL,
    )
    to_player = fields.ForeignKeyField(
        "models.Player",
        related_name="transactions_received",
        null=True,
        on_delete=fields.SET_NULL,
    )
    amount = fields.IntField()
    transaction_type = fields.CharEnumField(TransactionType, max_length=32)
    description = fields.TextField()
    related_entity_type = fields.CharField(max_length=64, null=True)
    related_entity_id = fields.BigIntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "transactions"
        indexes = (
            "from_player",
            "to_player",
            "transaction_type",
            "created_at",
        )
