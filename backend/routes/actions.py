from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
import httpx

from services.gemini_actions import generate_action_output
from services.graph_api import get_chats, get_chat_messages, get_emails, get_user_profile
from utils.mongodb import get_db
from utils.settings import settings

router = APIRouter(prefix="/actions", tags=["actions"])


class ActionRunRequest(BaseModel):
    action_id: str


def _resolve_token(request: Request, authorization: str | None, access_token: str | None) -> str:
    token = access_token or request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    return token


@router.get("/models")
async def list_models():
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="GEMINI_API_KEY is missing")

    url = f"https://generativelanguage.googleapis.com/v1/models?key={settings.GEMINI_API_KEY}"
    try:
        response = httpx.get(url, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Unable to list models: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list models: {str(exc)}")


@router.post("/run")
def run_action(
    payload: ActionRunRequest,
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    token = _resolve_token(request, authorization, access_token)

    user = get_user_profile(token)
    user_id = user.get("id") or user.get("userPrincipalName")

    emails_items: list[dict] = []
    chats_items: list[dict] = []
    messages_items: list[dict] = []

    db = get_db()
    if db is not None and user_id:
        emails_items = list(db.emails.find({"user_id": user_id}).sort("received_datetime", -1).limit(40))
        chats_items = list(db.chats.find({"user_id": user_id}).limit(30))
        messages_items = list(db.messages.find({"user_id": user_id}).sort("created_datetime", -1).limit(80))

    # Fallback to live Graph data if DB is empty
    if not emails_items and not chats_items and not messages_items:
        emails_items = get_emails(token).get("value", [])
        chats_items = get_chats(token).get("value", [])
        for chat in chats_items[:8]:
            chat_id = chat.get("id")
            if not chat_id:
                continue
            messages_items.extend(get_chat_messages(token, chat_id).get("value", []))

    output = generate_action_output(
        action_id=payload.action_id,
        user_profile=user,
        emails=emails_items,
        chats=chats_items,
        messages=messages_items,
    )

    return {
        "status": "success",
        "action_id": payload.action_id,
        "result": output,
        "stats": {
            "emails": len(emails_items),
            "chats": len(chats_items),
            "messages": len(messages_items),
        },
    }
