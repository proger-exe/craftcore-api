"""
User QOL router for scenarios, NPCs, and crafts
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from api.schemas.qol import (
    ScenarioResponse,
    ScenarioExecute,
    NPCResponse,
    NPCLocationSearch,
    CraftResponse,
)
from api.schemas.common import SuccessResponse
from api.dependencies import get_current_player, validate_pagination
from core.models.players.players import Player
from core.models.qol.scenarios import ScenarioType
from core.managers.qol.scenarios import (
    get_scenario,
    get_all_scenarios,
    execute_scenario,
)
from core.managers.qol.npcs import (
    get_npc,
    get_all_npcs,
    get_npcs_by_location,
    get_npc_dialog_by_id,
)
from core.managers.qol.crafts import (
    get_craft,
    get_all_crafts,
    get_crafts_by_item,
    can_craft,
)
from core.shared.logger import logger

router = APIRouter(prefix="/user", tags=["user", "qol"])


# Scenario endpoints


@router.get("/scenarios", response_model=List[ScenarioResponse])
async def get_scenarios_endpoint(
    scenario_type: Optional[ScenarioType] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get scenarios"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        scenarios = await get_all_scenarios(
            scenario_type=scenario_type,
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [ScenarioResponse.model_validate(s) for s in scenarios]
    except Exception as e:
        logger.error("Failed to get scenarios via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario_endpoint(
    scenario_id: int, player: Player = Depends(get_current_player)
):
    """Get scenario by ID"""
    scenario = await get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioResponse.model_validate(scenario)


@router.post("/scenarios/{scenario_id}/execute")
async def execute_scenario_endpoint(
    scenario_id: int,
    execute_data: ScenarioExecute,
    player: Player = Depends(get_current_player),
):
    """Execute a scenario"""
    try:
        scenario = await get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        result = await execute_scenario(
            scenario=scenario, player=player, args=execute_data.args
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute scenario via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# NPC endpoints


@router.get("/npcs", response_model=List[NPCResponse])
async def get_npcs_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get all NPCs"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        npcs = await get_all_npcs(
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [NPCResponse.model_validate(n) for n in npcs]
    except Exception as e:
        logger.error("Failed to get NPCs via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/npcs/{npc_id}", response_model=NPCResponse)
async def get_npc_endpoint(npc_id: int, player: Player = Depends(get_current_player)):
    """Get NPC by ID"""
    npc = await get_npc(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    return NPCResponse.model_validate(npc)


@router.get("/npcs/location", response_model=List[NPCResponse])
async def get_npcs_by_location_endpoint(
    dim: str = Query(...),
    x: float = Query(...),
    y: float = Query(...),
    z: float = Query(...),
    radius: float = Query(10.0, ge=0.1, le=100.0),
    player: Player = Depends(get_current_player),
):
    """Get NPCs by location"""
    try:
        npcs = await get_npcs_by_location(dim=dim, x=x, y=y, z=z, radius=radius)
        return [NPCResponse.model_validate(n) for n in npcs]
    except Exception as e:
        logger.error("Failed to get NPCs by location via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/npcs/{npc_id}/dialog/{message_id}", response_model=dict)
async def get_npc_dialog_endpoint(
    npc_id: int,
    message_id: str,
    player: Player = Depends(get_current_player),
):
    """Get NPC dialog by message ID"""
    try:
        npc = await get_npc(npc_id)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC not found")

        dialog_text = await get_npc_dialog_by_id(npc=npc, message_id=message_id)
        if dialog_text is None:
            raise HTTPException(status_code=404, detail="Dialog not found")

        return {"message_id": message_id, "text": dialog_text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get NPC dialog via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Craft endpoints


@router.get("/crafts", response_model=List[CraftResponse])
async def get_crafts_endpoint(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    player: Player = Depends(get_current_player),
):
    """Get all crafts"""
    try:
        pagination = validate_pagination(page=page, per_page=per_page)
        crafts = await get_all_crafts(
            limit=pagination["per_page"],
            offset=(pagination["page"] - 1) * pagination["per_page"],
        )
        return [CraftResponse.model_validate(c) for c in crafts]
    except Exception as e:
        logger.error("Failed to get crafts via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crafts/{craft_id}", response_model=CraftResponse)
async def get_craft_endpoint(
    craft_id: int, player: Player = Depends(get_current_player)
):
    """Get craft by ID"""
    craft = await get_craft(craft_id)
    if not craft:
        raise HTTPException(status_code=404, detail="Craft not found")
    return CraftResponse.model_validate(craft)


@router.get("/crafts/by-item/{item_id}", response_model=List[CraftResponse])
async def get_crafts_by_item_endpoint(
    item_id: str, player: Player = Depends(get_current_player)
):
    """Get crafts that use a specific item"""
    try:
        crafts = await get_crafts_by_item(item_id=item_id)
        return [CraftResponse.model_validate(c) for c in crafts]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to get crafts by item via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crafts/{craft_id}/can-craft", response_model=dict)
async def check_can_craft_endpoint(
    craft_id: int, player: Player = Depends(get_current_player)
):
    """Check if player can craft this item"""
    try:
        craft = await get_craft(craft_id)
        if not craft:
            raise HTTPException(status_code=404, detail="Craft not found")

        can_craft_result = await can_craft(craft=craft, player=player)
        return {"can_craft": can_craft_result, "craft_id": craft_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check can craft via API", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
