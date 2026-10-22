import asyncio
import sys

from core.models import init, close
from core.managers.players.players import (
    get_player,
    get_player_by_nickname,
    increase_player_balance,
    set_player_balance,
)
from core.managers.economics.transactions import create_transaction
from core.models.economics.transactions import TransactionType

DEFAULT_AMOUNT = 1000


def _usage() -> str:
    return (
        "Usage:\n"
        "  python grant_vaysh_to_nickname.py <nickname_or_id> [amount]\n"
        "  python grant_vaysh_to_nickname.py <nickname_or_id> =<amount>\n\n"
        "  nickname_or_id — ник игрока или числовой ID (например 777000)\n"
        "  amount         — добавить к балансу (default: 1000)\n"
        "  =amount        — установить баланс ровно в amount\n\n"
        "Examples:\n"
        "  python grant_vaysh_to_nickname.py Steve\n"
        "  python grant_vaysh_to_nickname.py 777000 =2000000000\n"
        "  python grant_vaysh_to_nickname.py Steve =5000\n"
    )


async def _run(nickname_or_id: str, amount: int, set_exact: bool) -> int:
    await init()
    try:
        # If first argument looks like numeric ID, get by id; otherwise by nickname
        if nickname_or_id.isdigit():
            player = await get_player(int(nickname_or_id))
        else:
            player = await get_player_by_nickname(nickname_or_id)
        if not player:
            print(f"Player '{nickname_or_id}' not found")
            return 2

        before_balance = player.balance
        label = str(player.id) if nickname_or_id.isdigit() else (player.nickname or str(player.id))
        if set_exact:
            updated = await set_player_balance(player, amount)
            print(
                f"Set balance for {label} to {amount}. "
                f"Was: {before_balance} -> {updated.balance}"
            )
        else:
            updated = await increase_player_balance(player, amount)
            await create_transaction(
                amount=amount,
                transaction_type=TransactionType.REWARD,
                description=f"Manual grant via script for {label}",
                from_player=None,
                to_player=updated,
            )
            print(
                f"Granted +{amount} vaysh to {label}. "
                f"Balance: {before_balance} -> {updated.balance}"
            )
        return 0
    finally:
        await close()


def main() -> int:
    if len(sys.argv) < 2:
        print(_usage())
        return 1

    nickname_or_id = sys.argv[1]
    amount = DEFAULT_AMOUNT
    set_exact = False

    if len(sys.argv) >= 3:
        arg = sys.argv[2]
        if arg.startswith("="):
            set_exact = True
            try:
                amount = int(arg[1:])
            except ValueError:
                print("Amount after '=' must be an integer")
                return 1
        else:
            try:
                amount = int(arg)
            except ValueError:
                print("Amount must be an integer")
                return 1

    if set_exact:
        if amount < 0:
            print("Balance cannot be negative")
            return 1
    else:
        if amount < 1:
            print("Amount must be greater than 0")
            return 1

    return asyncio.run(_run(nickname_or_id=nickname_or_id, amount=amount, set_exact=set_exact))


if __name__ == "__main__":
    raise SystemExit(main())
