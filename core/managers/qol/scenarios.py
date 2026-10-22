"""
Scenarios manager for CRUD operations on Scenario model
"""

from typing import Any, Optional, List, Dict, Union
from core.models.players.players import Player
from core.models.qol.scenarios import Scenario, ScenarioType
from core.shared.logger import logger
from core.shared.utils import to_id


async def create_scenario(
    name: str,
    scenario_type: ScenarioType,
    description: str = "",
    arguments: Optional[Dict] = None,
    command_stack: Optional[List] = None,
) -> Scenario:
    """
    Create a new scenario

    Args:
        name: Scenario name (max 32 chars)
        scenario_type: Scenario type (FIRST_JOIN, REGULAR, EVENT, ONE_TIME, OTHER)
        description: Scenario description (default: empty string)
        arguments: Arguments dict {required: [...], optional: [...]} (default: empty dict)
        command_stack: Command stack list (default: empty list)

    Returns:
        Scenario: Created scenario instance

    Raises:
        Exception: If creation fails
    """
    try:
        scenario = await Scenario.create(
            name=name,
            scenario_type=scenario_type,
            description=description,
            arguments=arguments or {},
            command_stack=command_stack or [],
        )
        logger.info(
            "📜 Scenario created",
            scenario_id=scenario.id,
            name=name,
            scenario_type=scenario_type.value,
        )
        return scenario
    except Exception as e:
        logger.error("Failed to create scenario", error=str(e), name=name)
        raise


async def get_scenario(scenario: Union[int, Scenario]) -> Optional[Scenario]:
    """
    Get scenario by ID или по экземпляру Scenario.

    Args:
        scenario: id сценария (int) или экземпляр Scenario

    Returns:
        Scenario or None if not found
    """
    try:
        sid = to_id(scenario)
        return await Scenario.get_or_none(id=sid)
    except Exception as e:
        logger.error(
            "Failed to get scenario", error=str(e), scenario_id=to_id(scenario)
        )
        raise


async def get_all_scenarios(
    scenario_type: Optional[ScenarioType] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Scenario]:
    """
    Get all scenarios

    Args:
        scenario_type: Filter by scenario type (optional)
        limit: Maximum number of scenarios to return
        offset: Number of scenarios to skip

    Returns:
        List of Scenario instances
    """
    try:
        query = Scenario.all()

        if scenario_type is not None:
            query = query.filter(scenario_type=scenario_type)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get all scenarios", error=str(e))
        raise


async def get_scenario_by_name(name: str) -> Optional[Scenario]:
    """
    Get scenario by name

    Args:
        name: Scenario name

    Returns:
        Scenario or None if not found
    """
    try:
        return await Scenario.get_or_none(name=name)
    except Exception as e:
        logger.error("Failed to get scenario by name", error=str(e), name=name)
        raise


async def get_scenarios_by_type(scenario_type: ScenarioType) -> List[Scenario]:
    """
    Get scenarios by type

    Args:
        scenario_type: Scenario type

    Returns:
        List of Scenario instances
    """
    try:
        return await Scenario.filter(scenario_type=scenario_type).order_by(
            "-created_at"
        )
    except Exception as e:
        logger.error(
            "Failed to get scenarios by type",
            error=str(e),
            scenario_type=scenario_type.value,
        )
        raise


async def update_scenario(
    scenario: Scenario,
    name: Optional[str] = None,
    description: Optional[str] = None,
    scenario_type: Optional[ScenarioType] = None,
    arguments: Optional[Dict] = None,
    command_stack: Optional[List] = None,
) -> Scenario:
    """
    Update scenario fields

    Args:
        scenario: Scenario instance to update
        name: New name (optional)
        description: New description (optional)
        scenario_type: New scenario type (optional)
        arguments: New arguments (optional)
        command_stack: New command stack (optional)

    Returns:
        Updated Scenario instance

    Raises:
        Exception: If update fails
    """
    try:
        if name is not None:
            scenario.name = name
        if description is not None:
            scenario.description = description
        if scenario_type is not None:
            scenario.scenario_type = scenario_type
        if arguments is not None:
            scenario.arguments = arguments
        if command_stack is not None:
            scenario.command_stack = command_stack

        await scenario.save()
        logger.info("🔄 Scenario updated", scenario_id=scenario.id)
        return scenario
    except Exception as e:
        logger.error("Failed to update scenario", error=str(e), scenario_id=scenario.id)
        raise


async def add_scenario_command(
    scenario: Scenario,
    command_name: str,
    args: List,
) -> Scenario:
    """
    Add command to scenario command stack

    Args:
        scenario: Scenario instance
        command_name: Command name
        args: Command arguments

    Returns:
        Updated Scenario instance

    Raises:
        Exception: If update fails
    """
    try:
        command_stack = scenario.command_stack or []
        command_stack.append({command_name: args})
        scenario.command_stack = command_stack
        await scenario.save()
        logger.info(
            "➕ Command added to scenario",
            scenario_id=scenario.id,
            command_name=command_name,
        )
        return scenario
    except Exception as e:
        logger.error(
            "Failed to add command to scenario",
            error=str(e),
            scenario_id=scenario.id,
        )
        raise


async def remove_scenario_command(scenario: Scenario, command_index: int) -> Scenario:
    """
    Remove command from scenario command stack by index

    Args:
        scenario: Scenario instance
        command_index: Index of command to remove

    Returns:
        Updated Scenario instance

    Raises:
        IndexError: If command_index is out of range
        Exception: If update fails
    """
    try:
        command_stack = scenario.command_stack or []
        if command_index < 0 or command_index >= len(command_stack):
            raise IndexError(f"Command index {command_index} is out of range")
        command_stack.pop(command_index)
        scenario.command_stack = command_stack
        await scenario.save()
        logger.info(
            "➖ Command removed from scenario",
            scenario_id=scenario.id,
            command_index=command_index,
        )
        return scenario
    except Exception as e:
        logger.error(
            "Failed to remove command from scenario",
            error=str(e),
            scenario_id=scenario.id,
        )
        raise


async def delete_scenario(scenario: Scenario) -> None:
    """
    Delete scenario

    Args:
        scenario: Scenario instance to delete

    Raises:
        Exception: If deletion fails
    """
    try:
        scenario_id = scenario.id
        await scenario.delete()
        logger.info("🗑️ Scenario deleted", scenario_id=scenario_id)
    except Exception as e:
        logger.error("Failed to delete scenario", error=str(e), scenario_id=scenario_id)
        raise


async def validate_scenario_args(scenario: Scenario, args: Dict) -> bool:
    """
    Validate scenario arguments against required and optional arguments

    Args:
        scenario: Scenario instance
        args: Arguments dictionary to validate

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails
    """
    try:
        from core.shared.validators import validate_json_structure

        required = scenario.arguments.get("required", [])
        optional = scenario.arguments.get("optional", [])

        # Check required arguments
        for req_arg in required:
            if isinstance(req_arg, list) and len(req_arg) >= 1:
                arg_name = req_arg[0]
                if arg_name not in args:
                    raise ValueError(f"Missing required argument: {arg_name}")

        # All provided arguments should be in required or optional
        all_allowed = [
            arg[0] if isinstance(arg, list) else arg for arg in required + optional
        ]
        for arg_name in args.keys():
            if arg_name not in all_allowed:
                raise ValueError(f"Unknown argument: {arg_name}")

        return True
    except Exception as e:
        logger.error(
            "Failed to validate scenario args", error=str(e), scenario_id=scenario.id
        )
        raise


async def execute_scenario(
    scenario: Scenario, player: Player, args: Dict
) -> Dict[str, Any]:
    """
    Execute scenario with provided arguments

    Args:
        scenario: Scenario instance
        player: Player instance
        args: Arguments dictionary

    Returns:
        Dictionary with execution results

    Raises:
        ValueError: If arguments are invalid
        Exception: If execution fails
    """
    try:
        # Validate arguments
        await validate_scenario_args(scenario, args)

        # Execute command stack
        results = []
        for cmd_dict in scenario.command_stack:
            command_name = list(cmd_dict.keys())[0]
            command_args = cmd_dict[command_name]

            # Replace placeholders in args with actual values
            processed_args = []
            for arg in command_args:
                if isinstance(arg, str) and arg.startswith("${") and arg.endswith("}"):
                    # Placeholder: ${arg_name}
                    placeholder = arg[2:-1]
                    if placeholder in args:
                        processed_args.append(args[placeholder])
                    else:
                        processed_args.append(arg)
                else:
                    processed_args.append(arg)

            results.append(
                {
                    "command": command_name,
                    "args": processed_args,
                    "status": "pending",  # In real implementation, would execute command
                }
            )

        logger.info(
            "▶️ Scenario executed",
            scenario_id=scenario.id,
            player_id=player.id,
            commands_count=len(results),
        )

        return {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "player_id": player.id,
            "commands_executed": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(
            "Failed to execute scenario",
            error=str(e),
            scenario_id=scenario.id,
            player_id=player.id,
        )
        raise
