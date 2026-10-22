"""
QOL schemas for scenarios, NPCs, and crafts
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from core.models.qol.scenarios import ScenarioType


class ScenarioCreate(BaseModel):
    """Schema for creating a scenario"""

    name: str
    scenario_type: ScenarioType
    description: str = ""
    arguments: Optional[Dict[str, Any]] = None
    command_stack: Optional[List[Dict[str, Any]]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "first_join_welcome",
                "scenario_type": "first_join",
                "description": "Welcome scenario for new players",
                "arguments": {"required": [["player_name", "str"]], "optional": []},
                "command_stack": [{"send_message": ["Welcome ${player_name}!"]}],
            }
        }


class ScenarioResponse(BaseModel):
    """Schema for scenario response"""

    id: int
    name: str
    description: str
    arguments: Dict[str, Any]
    command_stack: List[Dict[str, Any]]
    scenario_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario"""

    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[ScenarioType] = None
    arguments: Optional[Dict[str, Any]] = None
    command_stack: Optional[List[Dict[str, Any]]] = None


class ScenarioCommandAdd(BaseModel):
    """Schema for adding a command to a scenario's command stack"""

    command_name: str
    args: List[Any]


class ScenarioExecute(BaseModel):
    """Schema for executing a scenario"""

    args: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "args": {
                    "player_name": "Player123",
                }
            }
        }


class NPCCreate(BaseModel):
    """Schema for creating an NPC"""

    name: str
    description: str = ""
    locate: Optional[List] = None  # [dim, x, y, z]
    dialog: Optional[Dict[str, str]] = None
    skin: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Merchant",
                "description": "A friendly merchant",
                "locate": ["overworld", 100, 64, 200],
                "dialog": {"greeting": "Hello, traveler!"},
                "skin": "https://example.com/skin.png",
            }
        }


class NPCResponse(BaseModel):
    """Schema for NPC response"""

    id: int
    name: str
    description: str
    locate: List
    dialog: Dict[str, str]
    skin: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NPCUpdate(BaseModel):
    """Schema for updating an NPC"""

    name: Optional[str] = None
    description: Optional[str] = None
    locate: Optional[List] = None
    dialog: Optional[Dict[str, str]] = None
    skin: Optional[str] = None


class NPCLocationSearch(BaseModel):
    """Schema for NPC location search"""

    dim: str
    x: float
    y: float
    z: float
    radius: float = 10.0


class CraftCreate(BaseModel):
    """Schema for creating a craft"""

    icon: str
    name: str
    description: str = ""
    recipe: Optional[List[Dict[str, Any]]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "icon": "https://example.com/icon.png",
                "name": "Diamond Sword",
                "description": "A powerful sword",
                "recipe": [
                    {"item_id": "minecraft:diamond", "quantity": 2},
                    {"item_id": "minecraft:stick", "quantity": 1},
                ],
            }
        }


class CraftResponse(BaseModel):
    """Schema for craft response"""

    id: int
    icon: str
    name: str
    description: str
    recipe: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CraftUpdate(BaseModel):
    """Schema for updating a craft"""

    icon: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    recipe: Optional[List[Dict[str, Any]]] = None
