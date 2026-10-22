"""
Utility functions for common operations
"""

from typing import List, Optional, Any, Dict, Union
from datetime import datetime


def to_id(value: Union[int, Any]) -> int:
    """
    Coerce a model instance or its raw id to a plain int id.

    Accepts either an int (already an id) or any object with an `.id`
    attribute (e.g. a Tortoise model instance).
    """
    return int(value) if isinstance(value, int) else int(value.id)


def validate_string(
    value: str, min_length: int = 0, max_length: Optional[int] = None
) -> str:
    """
    Validate string with length checks

    Args:
        value: String to validate
        min_length: Minimum length (default: 0)
        max_length: Maximum length (optional)

    Returns:
        Validated string

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    if len(value) < min_length:
        raise ValueError(f"String must be at least {min_length} characters long")
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"String must be at most {max_length} characters long")
    return value


def validate_json_structure(data: dict, required_keys: List[str]) -> bool:
    """
    Validate JSON structure has required keys

    Args:
        data: Dictionary to validate
        required_keys: List of required keys

    Returns:
        True if valid

    Raises:
        ValueError: If required keys are missing
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")
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


def format_money(amount: int) -> str:
    """
    Format money amount as string

    Args:
        amount: Money amount

    Returns:
        Formatted string (e.g., "1,000" or "1,000,000")
    """
    return f"{amount:,}"


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string

    Args:
        dt: Datetime object
        format_str: Format string (default: "%Y-%m-%d %H:%M:%S")

    Returns:
        Formatted string
    """
    return dt.strftime(format_str)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def search_by_name(query: str, items: List[Any], name_attr: str = "name") -> List[Any]:
    """
    Search items by name (case-insensitive)

    Args:
        query: Search query
        items: List of items to search
        name_attr: Attribute name to search (default: "name")

    Returns:
        List of matching items
    """
    if not query:
        return items
    query_lower = query.lower()
    return [
        item
        for item in items
        if hasattr(item, name_attr)
        and query_lower in getattr(item, name_attr, "").lower()
    ]
