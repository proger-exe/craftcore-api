"""
Module of quality of life models
Objects:
- Crafts (deps: /app/routers/crafts.py, /bot/module/crafts, /dis_bot/module/crafts)
- NPCs (deps: /app/routers/npcs.py, /bot/module/npcs, /dis_bot/module/npcs)
- Scenarios (deps: /app/routers/scenarios.py, /bot/module/scenarios, /dis_bot/module/scenarios)
"""

from .crafts import Craft
from .npcs import NPC
from .scenarios import Scenario, ScenarioType

models = [
    "core.models.qol.crafts",
    "core.models.qol.npcs",
    "core.models.qol.scenarios",
]
