"""
Validators for model fields and data structures
"""

import re
from typing import List, Dict, Any


def validate_nickname(nickname: str) -> bool:
    """
    Validate Minecraft nickname

    Args:
        nickname: Nickname to validate

    Returns:
        True if valid

    Raises:
        ValueError: If nickname is invalid
    """
    if not nickname:
        raise ValueError("Nickname cannot be empty")
    if len(nickname) < 3:
        raise ValueError("Nickname must be at least 3 characters long")
    if len(nickname) > 16:
        raise ValueError("Nickname must be at most 16 characters long")
    if not re.match(r"^[a-zA-Z0-9_]+$", nickname):
        raise ValueError("Nickname can only contain letters, numbers, and underscores")
    return True


def validate_item_id(item_id: str) -> bool:
    """
    Validate Minecraft item ID format (e.g., minecraft:stone)

    Args:
        item_id: Item ID to validate

    Returns:
        True if valid

    Raises:
        ValueError: If item ID is invalid
    """
    if not item_id:
        raise ValueError("Item ID cannot be empty")
    if ":" not in item_id:
        raise ValueError(
            "Item ID must be in format 'namespace:item' (e.g., minecraft:stone)"
        )
    namespace, item = item_id.split(":", 1)
    if not namespace or not item:
        raise ValueError("Item ID namespace and item cannot be empty")
    if not re.match(r"^[a-z0-9_]+$", namespace):
        raise ValueError(
            "Item ID namespace can only contain lowercase letters, numbers, and underscores"
        )
    if not re.match(r"^[a-z0-9_]+$", item):
        raise ValueError(
            "Item ID name can only contain lowercase letters, numbers, and underscores"
        )
    return True


def validate_coordinates(coords: List) -> bool:
    """
    Validate coordinates format [dim, x, y, z]

    Args:
        coords: Coordinates list

    Returns:
        True if valid

    Raises:
        ValueError: If coordinates are invalid
    """
    if not isinstance(coords, list):
        raise ValueError("Coordinates must be a list")
    if len(coords) != 4:
        raise ValueError("Coordinates must have 4 elements: [dim, x, y, z]")
    dim, x, y, z = coords
    if not isinstance(dim, str):
        raise ValueError("Dimension must be a string")
    if not all(isinstance(coord, (int, float)) for coord in [x, y, z]):
        raise ValueError("Coordinates x, y, z must be numbers")
    return True


def validate_recipe(recipe: List) -> bool:
    """
    Validate craft recipe format

    Args:
        recipe: Recipe list (item_id: [id, quantity])

    Returns:
        True if valid

    Raises:
        ValueError: If recipe is invalid
    """
    if not isinstance(recipe, list):
        raise ValueError("Recipe must be a list")
    for item in recipe:
        if not isinstance(item, dict):
            raise ValueError("Recipe items must be dictionaries")
        if "item_id" not in item:
            raise ValueError("Recipe item must have 'item_id' field")
        if "quantity" not in item:
            raise ValueError("Recipe item must have 'quantity' field")
        validate_item_id(item["item_id"])
        if not isinstance(item["quantity"], int) or item["quantity"] < 1:
            raise ValueError("Recipe item quantity must be a positive integer")
    return True


def validate_command_stack(commands: List) -> bool:
    """
    Validate command stack format

    Args:
        commands: Command stack list [command_name: [args]]

    Returns:
        True if valid

    Raises:
        ValueError: If command stack is invalid
    """
    if not isinstance(commands, list):
        raise ValueError("Command stack must be a list")
    for cmd in commands:
        if not isinstance(cmd, dict):
            raise ValueError("Commands must be dictionaries")
        if len(cmd) != 1:
            raise ValueError("Command must have exactly one key (command name)")
        command_name = list(cmd.keys())[0]
        if not isinstance(command_name, str):
            raise ValueError("Command name must be a string")
        args = cmd[command_name]
        if not isinstance(args, list):
            raise ValueError("Command arguments must be a list")
    return True
