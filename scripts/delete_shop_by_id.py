"""
Скрипт удаления любого шопа по ID.
"""

import asyncio
import sys

from core.models import init, close
from core.managers.economics.shops import get_shop, delete_shop


def _usage() -> str:
    return (
        "Usage:\n"
        "  python delete_shop_by_id.py <shop_id>\n\n"
        "  Удаляет магазин с указанным ID (любой владелец).\n"
        "  shop_id — числовой ID магазина.\n\n"
        "Example:\n"
        "  python delete_shop_by_id.py 42\n"
    )


async def _run(shop_id: int) -> int:
    await init()
    try:
        shop = await get_shop(shop_id)
        if not shop:
            print(f"Shop with id {shop_id} not found")
            return 2

        await delete_shop(shop)
        print(f"Shop {shop_id} deleted successfully")
        return 0
    finally:
        await close()


def main() -> int:
    if len(sys.argv) < 2:
        print(_usage())
        return 1

    try:
        shop_id = int(sys.argv[1])
    except ValueError:
        print("shop_id must be an integer")
        return 1

    if shop_id < 1:
        print("shop_id must be positive")
        return 1

    return asyncio.run(_run(shop_id=shop_id))


if __name__ == "__main__":
    sys.exit(main())
