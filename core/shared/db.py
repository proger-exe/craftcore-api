"""
Shared DB helpers — locking convention for state mutation.

Most read-modify-write mutations in this repo (JSON-array membership fields,
status flags, etc.) fetch an ORM row unlocked, mutate it in Python, then
`.save()` it — a lost-update race under concurrent requests. The only correct
reference pattern in the repo is `core/managers/economics/transactions.py`'s
`transfer_between_players`/`grant_reward`, which lock the row with
`select_for_update()` inside a transaction first. `locked_row` is that same
pattern factored into one reusable helper for single-row mutations.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, TypeVar

from tortoise.models import Model
from tortoise.transactions import in_transaction

ModelT = TypeVar("ModelT", bound=Model)


@asynccontextmanager
async def locked_row(model_cls: type[ModelT], **filters) -> AsyncIterator[ModelT]:
    """
    Open a transaction and yield a `select_for_update()`-locked row.

    Usage:
        async with locked_row(Clan, id=clan.id) as locked_clan:
            locked_clan.members.append(player.id)
            await locked_clan.save(update_fields=["members"])

    Raises ValueError if no row matches the given filters.
    """
    async with in_transaction() as conn:
        obj = await model_cls.filter(**filters).using_db(conn).select_for_update().first()
        if obj is None:
            raise ValueError(f"{model_cls.__name__} not found")
        yield obj
