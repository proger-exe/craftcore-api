"""
Service auth schemas — issuing JWTs to trusted backend services (bots, admin panel).
"""

from pydantic import BaseModel


class ServiceTokenRequest(BaseModel):
    """Credentials for a registered backend service (see SERVICE_CREDENTIALS in .env)."""

    client_id: str
    client_secret: str


class ServiceTokenResponse(BaseModel):
    """Short-lived bearer token identifying the calling service."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
