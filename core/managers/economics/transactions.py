"""
Transactions manager for CRUD operations on Transaction model
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from tortoise.expressions import Q
from tortoise.transactions import in_transaction
from core.models.economics.transactions import Transaction, TransactionType
from core.models.players.players import Player
from core.shared.logger import logger
from core.shared.utils import to_id
from core.managers.economics.utils import validate_amount


async def transfer_between_players(
    from_player: Player,
    to_player: Player,
    amount: int,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Safely transfer balance between players in a single DB transaction.

    Rules:
    - amount must be > 0
    - sender and receiver must be different players
    - sender must have enough balance
    """
    amount = validate_amount(amount=amount)
    if amount < 1:
        raise ValueError("Amount must be greater than 0")
    if from_player.id == to_player.id:
        raise ValueError("Cannot transfer to yourself")

    transfer_description = (
        description or f"Transfer from {from_player.id} to {to_player.id}"
    )

    try:
        async with in_transaction() as conn:
            player_ids = sorted([int(from_player.id), int(to_player.id)])
            locked_players = (
                await Player.filter(id__in=player_ids)
                .using_db(conn)
                .select_for_update()
                .all()
            )
            if len(locked_players) != 2:
                raise ValueError("Player not found")

            locked_by_id = {int(p.id): p for p in locked_players}
            locked_from = locked_by_id[int(from_player.id)]
            locked_to = locked_by_id[int(to_player.id)]

            available_from = locked_from.balance - getattr(
                locked_from, "frozen_balance", 0
            )
            if available_from < amount:
                raise ValueError("Insufficient balance")

            locked_from.balance -= amount
            locked_to.balance += amount

            await locked_from.save(update_fields=["balance"], using_db=conn)
            await locked_to.save(update_fields=["balance"], using_db=conn)

            transaction = await Transaction.create(
                from_player=locked_from,
                to_player=locked_to,
                amount=amount,
                transaction_type=TransactionType.TRANSFER,
                description=transfer_description,
                using_db=conn,
            )

        logger.info(
            "💸 Transfer completed",
            transaction_id=transaction.id,
            from_player_id=from_player.id,
            to_player_id=to_player.id,
            amount=amount,
        )
        return {
            "transaction": transaction,
            "from_balance_after": locked_from.balance,
            "to_balance_after": locked_to.balance,
        }
    except Exception as e:
        logger.error(
            "Failed to transfer between players",
            error=str(e),
            from_player_id=from_player.id,
            to_player_id=to_player.id,
            amount=amount,
        )
        raise


async def create_transaction(
    amount: int,
    transaction_type: TransactionType,
    description: str,
    from_player: Optional[Player] = None,
    to_player: Optional[Player] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> Transaction:
    """
    Create a new transaction

    Args:
        amount: Transaction amount
        transaction_type: Type of transaction
        description: Transaction description
        from_player: Sender player (optional, None for system transactions)
        to_player: Receiver player (optional, None for system transactions)
        related_entity_type: Type of related entity (optional)
        related_entity_id: ID of related entity (optional)

    Returns:
        Transaction: Created transaction instance

    Raises:
        ValueError: If amount is negative or both players are None
        Exception: If creation fails
    """
    amount = validate_amount(amount=amount)
    if from_player is None and to_player is None:
        raise ValueError(
            "At least one player (from_player or to_player) must be specified"
        )

    try:
        transaction = await Transaction.create(
            from_player=from_player,
            to_player=to_player,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        logger.info(
            "💰 Transaction created",
            transaction_id=transaction.id,
            transaction_type=transaction_type.value,
            amount=amount,
        )
        return transaction
    except Exception as e:
        logger.error("Failed to create transaction", error=str(e), amount=amount)
        raise


async def grant_reward(
    player: Player,
    amount: int,
    description: str = "Daily reward",
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Grant a system reward to a player in a single DB transaction.

    - Increases player balance by `amount`
    - Creates Transaction with type REWARD and from_player=None, to_player=player
    """
    amount = validate_amount(amount=amount)
    if amount < 1:
        raise ValueError("Amount must be greater than 0")

    try:
        async with in_transaction() as conn:
            locked_player = (
                await Player.filter(id=player.id)
                .using_db(conn)
                .select_for_update()
                .first()
            )
            if not locked_player:
                raise ValueError("Player not found")

            locked_player.balance += amount
            await locked_player.save(update_fields=["balance"], using_db=conn)

            transaction = await Transaction.create(
                from_player=None,
                to_player=locked_player,
                amount=amount,
                transaction_type=TransactionType.REWARD,
                description=description,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                using_db=conn,
            )

        logger.info(
            "💰 Reward granted",
            transaction_id=transaction.id,
            player_id=player.id,
            amount=amount,
            balance_after=locked_player.balance,
            description=description,
        )
        return {"transaction": transaction, "balance_after": locked_player.balance}
    except Exception as e:
        logger.error(
            "Failed to grant reward",
            error=str(e),
            player_id=player.id,
            amount=amount,
            description=description,
        )
        raise


async def get_transaction(
    transaction: Union[int, Transaction],
) -> Optional[Transaction]:
    """
    Get transaction by ID или по экземпляру Transaction.

    Args:
        transaction: id транзакции (int) или экземпляр Transaction

    Returns:
        Transaction or None if not found
    """
    try:
        tid = to_id(transaction)
        return await Transaction.get_or_none(id=tid)
    except Exception as e:
        logger.error(
            "Failed to get transaction",
            error=str(e),
            transaction_id=to_id(transaction),
        )
        raise


async def get_player_transactions(
    player: Player,
    as_sender: bool = True,
    as_receiver: bool = True,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Transaction]:
    """
    Get all transactions for player

    Args:
        player: Player instance
        as_sender: Include transactions where player is sender
        as_receiver: Include transactions where player is receiver
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip

    Returns:
        List of Transaction instances
    """
    try:
        if as_sender and as_receiver:
            query = Transaction.filter(
                Q(from_player_id=player.id) | Q(to_player_id=player.id)
            )
        elif as_sender:
            query = Transaction.filter(from_player=player)
        elif as_receiver:
            query = Transaction.filter(to_player=player)
        else:
            return []

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error(
            "Failed to get player transactions", error=str(e), player_id=player.id
        )
        raise


async def get_transactions_by_type(
    transaction_type: TransactionType,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Transaction]:
    """
    Get transactions by type

    Args:
        transaction_type: Type of transaction
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip

    Returns:
        List of Transaction instances
    """
    try:
        query = Transaction.filter(transaction_type=transaction_type)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error(
            "Failed to get transactions by type",
            error=str(e),
            transaction_type=transaction_type.value,
        )
        raise


async def get_transactions_by_date_range(
    start_date: datetime,
    end_date: datetime,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Transaction]:
    """
    Get transactions by date range

    Args:
        start_date: Start date
        end_date: End date
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip

    Returns:
        List of Transaction instances
    """
    try:
        query = Transaction.filter(created_at__gte=start_date, created_at__lte=end_date)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get transactions by date range", error=str(e))
        raise


async def get_transaction_statistics(
    player: Optional[Player] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """
    Get transaction statistics

    Args:
        player: Filter by player (optional)
        transaction_type: Filter by type (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)

    Returns:
        Dictionary with statistics:
        - total_count: Total number of transactions
        - total_amount: Total amount
        - incoming_amount: Total incoming amount (for player)
        - outgoing_amount: Total outgoing amount (for player)
    """
    try:
        query = Transaction.all()

        if player is not None:
            query = query.filter(
                Q(from_player_id=player.id) | Q(to_player_id=player.id)
            )
        if transaction_type is not None:
            query = query.filter(transaction_type=transaction_type)
        if start_date is not None:
            query = query.filter(created_at__gte=start_date)
        if end_date is not None:
            query = query.filter(created_at__lte=end_date)

        transactions = await query.all()

        total_count = len(transactions)
        total_amount = sum(t.amount for t in transactions)

        incoming_amount = 0
        outgoing_amount = 0

        if player is not None:
            for t in transactions:
                if t.to_player and t.to_player.id == player.id:
                    incoming_amount += t.amount
                if t.from_player and t.from_player.id == player.id:
                    outgoing_amount += t.amount

        return {
            "total_count": total_count,
            "total_amount": total_amount,
            "incoming_amount": incoming_amount,
            "outgoing_amount": outgoing_amount,
        }
    except Exception as e:
        logger.error("Failed to get transaction statistics", error=str(e))
        raise


async def get_transactions(
    from_player: Optional[Player] = None,
    to_player: Optional[Player] = None,
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Transaction]:
    """
    Get transactions with multiple filters

    Args:
        from_player: Filter by sender (optional)
        to_player: Filter by receiver (optional)
        transaction_type: Filter by type (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip

    Returns:
        List of Transaction instances
    """
    try:
        query = Transaction.all()

        if from_player is not None:
            query = query.filter(from_player=from_player)
        if to_player is not None:
            query = query.filter(to_player=to_player)
        if transaction_type is not None:
            query = query.filter(transaction_type=transaction_type)
        if start_date is not None:
            query = query.filter(created_at__gte=start_date)
        if end_date is not None:
            query = query.filter(created_at__lte=end_date)

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return await query.order_by("-created_at")
    except Exception as e:
        logger.error("Failed to get transactions", error=str(e))
        raise


async def create_bulk_transactions(transactions: List[dict]) -> List[Transaction]:
    """
    Create bulk transactions

    Args:
        transactions: List of transaction dictionaries
            Each dict should contain: amount, transaction_type, description,
            from_player, to_player, related_entity_type, related_entity_id

    Returns:
        List of created Transaction instances

    Raises:
        Exception: If creation fails
    """
    try:
        created_transactions = []
        for data in transactions:
            transaction = await create_transaction(
                amount=data["amount"],
                transaction_type=data["transaction_type"],
                description=data["description"],
                from_player=data.get("from_player"),
                to_player=data.get("to_player"),
                related_entity_type=data.get("related_entity_type"),
                related_entity_id=data.get("related_entity_id"),
            )
            created_transactions.append(transaction)
        logger.info("💰 Bulk transactions created", count=len(created_transactions))
        return created_transactions
    except Exception as e:
        logger.error("Failed to create bulk transactions", error=str(e))
        raise


async def get_player_balance_history(
    player: Player, days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get player balance history over time

    Args:
        player: Player instance
        days: Number of days to look back (default: 30)

    Returns:
        List of dictionaries with date and balance change
    """
    try:
        from datetime import timedelta
        from core.shared.utils import format_datetime, format_money

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        transactions = await get_player_transactions(
            player, as_sender=True, as_receiver=True
        )

        # Filter by date range
        filtered = [t for t in transactions if start_date <= t.created_at <= end_date]

        # Group by date and calculate daily changes
        daily_changes = {}
        for trans in filtered:
            date_key = trans.created_at.date().isoformat()
            if date_key not in daily_changes:
                daily_changes[date_key] = {"incoming": 0, "outgoing": 0}

            if trans.to_player and trans.to_player.id == player.id:
                daily_changes[date_key]["incoming"] += trans.amount
            if trans.from_player and trans.from_player.id == player.id:
                daily_changes[date_key]["outgoing"] += trans.amount

        # Format result
        history = []
        for date, changes in sorted(daily_changes.items()):
            history.append(
                {
                    "date": date,
                    "incoming": changes["incoming"],
                    "outgoing": changes["outgoing"],
                    "net": changes["incoming"] - changes["outgoing"],
                }
            )

        return history
    except Exception as e:
        logger.error(
            "Failed to get player balance history", error=str(e), player_id=player.id
        )
        raise


async def get_top_players_by_balance(limit: int = 10) -> List[Player]:
    """
    Get top players by balance

    Args:
        limit: Number of top players to return (default: 10)

    Returns:
        List of Player instances sorted by balance (descending)
    """
    try:
        # Exclude system owner (id=777000) from public rankings.
        return (
            await Player.filter()
            .exclude(id=777000)
            .order_by("-balance")
            .limit(limit)
        )
    except Exception as e:
        logger.error("Failed to get top players by balance", error=str(e))
        raise
