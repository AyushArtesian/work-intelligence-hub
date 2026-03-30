import urllib.parse

import httpx
from fastapi import HTTPException, status

from utils.settings import settings


def build_auth_url() -> str:
    tenant = settings.TENANT_ID
    base = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"

    # minimal scope for read-only data access
    scope = "openid profile offline_access User.Read Mail.Read Chat.Read ChatMessage.Read"

    params = {
        "client_id": settings.CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.REDIRECT_URI,
        "response_mode": "query",
        "scope": scope,
        "state": "work-intel-state",  # add CSRF state in production
    }

    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    token_url = f"https://login.microsoftonline.com/{settings.TENANT_ID}/oauth2/v2.0/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.REDIRECT_URI,
    }

    with httpx.Client(timeout=10) as client:
        response = client.post(token_url, data=data)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "token_exchange_failed", "detail": response.json()},
        )

    return response.json()
