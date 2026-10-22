from tortoise import fields
from tortoise.models import Model


class Shop(Model):
    """
    Base class of shop
    - `id` (`BigInt`) - id of Shop
    - `name` (`str`) - name of Shop
    - `owner` (`models.Player`) - Relation to Player model (who owns Shop?)
    """

    id = fields.BigIntField(pk=True)
    owner_id = fields.ForeignKeyField("models.Player", related_name="owner")
    name = fields.TextField(default="Shop")
    # inventory mirror by item_id:
    # {item_id: {"price": int, "quantity": int, "total_count": int}}
    inventory = fields.JSONField(default=dict)

    class Meta:
        table = "shops"


class ShopItem(Model):
    """
    Product in shop

    - `item_id` (`str`): ID of item in Minecraft, example: minecraft:stone
    - `item_nbt` (`str`): Optional NBT (e.g. JSON string); empty string = no NBT. Enchants, custom name, etc.
    - `shop` (`models.Shop`): Relation to Shop model
    - `price` (`int`): Item cost
    - `quantity` (`int`): Lot size (how many units one sale operation transfers)
    - `total_count` (`int`): Current total stock in this shop
    """

    item_id = fields.CharField(max_length=128)
    item_nbt = fields.TextField(
        default="", description="NBT data (e.g. JSON); empty = no NBT"
    )
    shop = fields.ForeignKeyField(
        "models.Shop", related_name="items", on_delete=fields.CASCADE
    )
    price = fields.IntField(default=0, description="Price per unit, >= 0")
    quantity = fields.IntField(default=1, description="Lot size, >= 1")
    total_count = fields.IntField(default=0, description="Current stock, >= 0")

    class Meta:
        table = "shop_items"
        unique_together = ("shop", "item_id", "item_nbt")
        indexes = ("shop", "item_id")
