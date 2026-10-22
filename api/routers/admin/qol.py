"""
Admin QOL router for managing scenarios, NPCs, and crafts
"""

from fastapi import APIRouter, Depends
from api.schemas.qol import (
    ScenarioCreate,
    ScenarioResponse,
    ScenarioUpdate,
    ScenarioCommandAdd,
    NPCCreate,
    NPCResponse,
    NPCUpdate,
    CraftCreate,
    CraftResponse,
    CraftUpdate,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_admin
from core.models.players.players import Player
from core.managers.qol.scenarios import (
    create_scenario,
    get_scenario,
    update_scenario,
    delete_scenario,
    add_scenario_command,
    remove_scenario_command,
)
from core.managers.qol.npcs import (
    create_npc,
    get_npc,
    update_npc,
    delete_npc,
)
from core.managers.qol.crafts import (
    create_craft,
    get_craft,
    update_craft,
    delete_craft,
)
from core.shared.errors import NotFoundError, ValidationError

router = APIRouter(prefix="/admin", tags=["admin", "qol"])


# Scenario management


@router.post("/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario_endpoint(
    scenario_data: ScenarioCreate,
    admin: Player = Depends(get_current_admin),
):
    """Create a new scenario"""
    scenario = await create_scenario(
        name=scenario_data.name,
        scenario_type=scenario_data.scenario_type,
        description=scenario_data.description,
        arguments=scenario_data.arguments,
        command_stack=scenario_data.command_stack,
    )
    return ScenarioResponse.model_validate(scenario)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario_endpoint(
    scenario_id: int,
    scenario_data: ScenarioUpdate,
    admin: Player = Depends(get_current_admin),
):
    """Update a scenario"""
    scenario = await get_scenario(scenario_id)
    if not scenario:
        raise NotFoundError("Scenario not found")

    updated = await update_scenario(
        scenario=scenario,
        name=scenario_data.name,
        description=scenario_data.description,
        scenario_type=scenario_data.scenario_type,
        arguments=scenario_data.arguments,
        command_stack=scenario_data.command_stack,
    )
    return ScenarioResponse.model_validate(updated)


@router.delete("/scenarios/{scenario_id}", response_model=SuccessResponse)
async def delete_scenario_endpoint(
    scenario_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete a scenario"""
    scenario = await get_scenario(scenario_id)
    if not scenario:
        raise NotFoundError("Scenario not found")

    await delete_scenario(scenario)
    return SuccessResponse(message="Scenario deleted successfully")


@router.post("/scenarios/{scenario_id}/commands", response_model=ScenarioResponse)
async def add_scenario_command_endpoint(
    scenario_id: int,
    command_data: ScenarioCommandAdd,
    admin: Player = Depends(get_current_admin),
):
    """Add a command to a scenario's command stack"""
    scenario = await get_scenario(scenario_id)
    if not scenario:
        raise NotFoundError("Scenario not found")

    updated = await add_scenario_command(
        scenario=scenario,
        command_name=command_data.command_name,
        args=command_data.args,
    )
    return ScenarioResponse.model_validate(updated)


@router.delete(
    "/scenarios/{scenario_id}/commands/{command_index}",
    response_model=ScenarioResponse,
)
async def remove_scenario_command_endpoint(
    scenario_id: int,
    command_index: int,
    admin: Player = Depends(get_current_admin),
):
    """Remove a command from a scenario's command stack by index"""
    scenario = await get_scenario(scenario_id)
    if not scenario:
        raise NotFoundError("Scenario not found")

    try:
        updated = await remove_scenario_command(
            scenario=scenario, command_index=command_index
        )
    except IndexError as e:
        raise ValidationError(str(e))
    return ScenarioResponse.model_validate(updated)


# NPC management


@router.post("/npcs", response_model=NPCResponse, status_code=201)
async def create_npc_endpoint(
    npc_data: NPCCreate,
    admin: Player = Depends(get_current_admin),
):
    """Create a new NPC"""
    npc = await create_npc(
        name=npc_data.name,
        description=npc_data.description,
        locate=npc_data.locate,
        dialog=npc_data.dialog,
        skin=npc_data.skin,
    )
    return NPCResponse.model_validate(npc)


@router.put("/npcs/{npc_id}", response_model=NPCResponse)
async def update_npc_endpoint(
    npc_id: int,
    npc_data: NPCUpdate,
    admin: Player = Depends(get_current_admin),
):
    """Update an NPC"""
    npc = await get_npc(npc_id)
    if not npc:
        raise NotFoundError("NPC not found")

    updated = await update_npc(
        npc=npc,
        name=npc_data.name,
        description=npc_data.description,
        locate=npc_data.locate,
        dialog=npc_data.dialog,
        skin=npc_data.skin,
    )
    return NPCResponse.model_validate(updated)


@router.delete("/npcs/{npc_id}", response_model=SuccessResponse)
async def delete_npc_endpoint(npc_id: int, admin: Player = Depends(get_current_admin)):
    """Delete an NPC"""
    npc = await get_npc(npc_id)
    if not npc:
        raise NotFoundError("NPC not found")

    await delete_npc(npc)
    return SuccessResponse(message="NPC deleted successfully")


# Craft management


@router.post("/crafts", response_model=CraftResponse, status_code=201)
async def create_craft_endpoint(
    craft_data: CraftCreate,
    admin: Player = Depends(get_current_admin),
):
    """Create a new craft"""
    craft = await create_craft(
        icon=craft_data.icon,
        name=craft_data.name,
        description=craft_data.description,
        recipe=craft_data.recipe,
    )
    return CraftResponse.model_validate(craft)


@router.put("/crafts/{craft_id}", response_model=CraftResponse)
async def update_craft_endpoint(
    craft_id: int,
    craft_data: CraftUpdate,
    admin: Player = Depends(get_current_admin),
):
    """Update a craft"""
    craft = await get_craft(craft_id)
    if not craft:
        raise NotFoundError("Craft not found")

    updated = await update_craft(
        craft=craft,
        icon=craft_data.icon,
        name=craft_data.name,
        description=craft_data.description,
        recipe=craft_data.recipe,
    )
    return CraftResponse.model_validate(updated)


@router.delete("/crafts/{craft_id}", response_model=SuccessResponse)
async def delete_craft_endpoint(
    craft_id: int, admin: Player = Depends(get_current_admin)
):
    """Delete a craft"""
    craft = await get_craft(craft_id)
    if not craft:
        raise NotFoundError("Craft not found")

    await delete_craft(craft)
    return SuccessResponse(message="Craft deleted successfully")
