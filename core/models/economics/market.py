from tortoise import fields
from tortoise.models import Model


class MarketItem(Model):
    """
    Item in market

    - `id` (`BigInt`): ID of item in market
    - `item_id` (`str`): ID of item in Minecraft, example: minecraft:stone
    - `seller` (`models.Player`): Relation to Player model
    - `name` (`str`): Name of position
    - `desc` (`str`): Description of position
    - `price` (`int`): Item cost
    - `quantity` (`int`): Item count
    """

    id = fields.BigIntField(pk=True)
    item_id = fields.CharField(max_length=128)
    seller = fields.ForeignKeyField("models.Player", related_name="market_items")
    name = fields.CharField(max_length=64)
    desc = fields.TextField()
    total_price = fields.IntField()
    quantity = fields.IntField()

    class Meta:
        table = "market_items"
        indexes = ("seller", "item_id", "total_price")
