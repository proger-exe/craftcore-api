"""
Typed exceptions for the router->HTTP boundary.

Replaces the copy-pasted per-router `except ValueError: ... / except Exception:
raise HTTPException(500, ...)` block. Routers raise these directly (or convert
a manager's ValueError at the router boundary during incremental rollout);
the handlers registered in main.py turn them into the matching HTTP response.
`HTTPException` keeps working untouched — FastAPI handles it natively.
"""


class AppError(Exception):
    status_code: int = 400

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class InsufficientBalanceError(AppError):
    status_code = 402


class ValidationError(AppError):
    status_code = 400
