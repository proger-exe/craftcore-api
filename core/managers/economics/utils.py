"""
Utility functions for economics managers
"""


def validate_amount(amount: int) -> None:
    """
    Validate that amount is positive

    Args:
        amount: Amount to validate

    Raises:
        ValueError: If amount is negative
    """
    if amount is not None and amount < 0:
        raise ValueError("Amount must be positive")
    return amount
