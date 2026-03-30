from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

from services.microsoft_auth import build_auth_url, exchange_code_for_token
from services.graph_api import get_user_profile
from utils.mongodb import get_db
from utils.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login():
    """Redirects user to Microsoft Azure AD login URL."""
    return RedirectResponse(build_auth_url())


@router.get("/callback")
def callback(code: str | None = None, state: str | None = None):
    """Receives authorization code from Azure AD and exchanges it for tokens."""
    if code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code in callback",
        )

    token_data = exchange_code_for_token(code)
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain access token from Microsoft.",
        )

    # Fetch profile and persist user + token
    profile = get_user_profile(access_token)
    user_id = profile.get("id") or profile.get("userPrincipalName")

    db = get_db()
    if db is not None:
        try:
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "user_id": user_id,
                        "email": profile.get("mail") or profile.get("userPrincipalName"),
                        "name": profile.get("displayName"),
                        "access_token": access_token,
                        "refresh_token": token_data.get("refresh_token"),
                        "expires_in": token_data.get("expires_in"),
                        "updated_at": __import__("datetime").datetime.utcnow(),
                    }
                },
                upsert=True,
            )
        except Exception as exc:
            print("[WARNING] Could not store user token in DB:", exc)

    # Set access token as secure cookie to keep the user logged in in browser.
    # (In production, use proper signed auth tokens and HTTPS only.)
    redirect_url = settings.FRONTEND_URL.rstrip("/") + "/dashboard"
    response = RedirectResponse(url=redirect_url)
    response.set_cookie(
        key="work_intel_access_token",
        value=access_token,
        httponly=True,
        secure=False,  # set True in production with HTTPS
        samesite="lax",
        max_age=3600,
    )

    # also return token payload as JSON via query for mobile/JS clients
    response.headers["X-Auth-Token"] = access_token

    return response


@router.get("/me")
def me(access_token: str | None = None, work_intel_access_token: str | None = None):
    """Return currently authenticated user by token from cookie or query."""
    token = access_token or work_intel_access_token
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_profile = get_user_profile(token)
    return user_profile


@router.post("/logout")
def logout():
    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie("work_intel_access_token")
    return response
