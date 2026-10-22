"""
Service token issuance for trusted backend integrations.
"""

import secrets

from fastapi import APIRouter, HTTPException

from api.schemas.auth import ServiceTokenRequest, ServiceTokenResponse
from core.shared.service_auth import create_service_token
from settings import settings

router = APIRouter(prefix="/integrations/auth", tags=["integrations", "auth"])


@router.post("/token", response_model=ServiceTokenResponse)
async def issue_service_token(payload: ServiceTokenRequest):
    """Exchange a registered service's client_id/client_secret for a JWT.

    Callers use the returned token as `Authorization: Bearer <token>` to act
    as the system account (X-Player-ID: 777000) — see api/dependencies.py.
    """
    expected_secret = settings.service_credentials.get(payload.client_id)
    if expected_secret is None or not secrets.compare_digest(
        expected_secret, payload.client_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    token = create_service_token(payload.client_id)
    return ServiceTokenResponse(
        access_token=token,
        expires_in=settings.JWT_SERVICE_TOKEN_TTL_MINUTES * 60,
    )
