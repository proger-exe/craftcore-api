"""
Module of economic system
Objects:
- Shops (deps: /app/routers/shops.py, /bot/module/shops, /dis_bot/module/shops)
- Market (deps: /app/routers/market.py, /bot/module/market, /dis_bot/module/market)
- Transactions (deps: /app/routers/transactions.py, /bot/module/transactions, /dis_bot/module/transactions)
- Quests (deps: /app/routers/quests.py, /bot/module/quests, /dis_bot/module/quests)
"""

from .shops import *
from .market import *
from .transactions import *
from .quests import *
from .player_quests import PlayerQuest, PlayerQuestApplication

models = [
    "core.models.economics.shops",
    "core.models.economics.market",
    "core.models.economics.transactions",
    "core.models.economics.quests",
    "core.models.economics.player_quests",
]
