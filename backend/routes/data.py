from fastapi import APIRouter, Header, Query, HTTPException, status

from services.graph_api import get_user_profile, get_emails, get_chats, get_chat_messages
from models.response_models import DataResponse
from utils.mongodb import get_db

router = APIRouter(prefix="/data", tags=["data"])


def _resolve_access_token(authorization: str | None, access_token: str | None) -> str:
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    if access_token:
        return access_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing access token. Provide in Authorization header or access_token query param.",
    )


@router.get("/fetch", response_model=DataResponse)
def fetch_data(
    authorization: str | None = Header(None), access_token: str | None = Query(None)
):
    """Fetches user profile, emails, chats, and chat messages from Microsoft Graph."""
    token = _resolve_access_token(authorization, access_token)

    user = get_user_profile(token)
    emails = get_emails(token)
    chats = get_chats(token)

    # for simplicity fetch messages from 1-2 recent chats
    chats_items = chats.get("value", [])
    chat_picks = chats_items[:2]

    messages = []
    for chat in chat_picks:
        chat_id = chat.get("id")
        if chat_id:
            chat_messages = get_chat_messages(token, chat_id)
            messages.append({"chat_id": chat_id, "messages": chat_messages.get("value", [])})

    # attempt to store a fetch record for debugging/connection verification
    db = get_db()
    if db is not None:
        try:
            db.fetch_history.insert_one(
                {
                    "user": user.get("userPrincipalName", user.get("mail", "unknown")),
                    "timestamp": __import__("datetime").datetime.utcnow(),
                    "emails_count": len(emails.get("value", [])),
                    "chats_count": len(chats_items),
                }
            )
        except Exception as exc:
            # do not fail the endpoint for DB issues; log for developer
            print("[WARNING] Unable to write fetch_history", exc)

    return {
        "user": user,
        "emails": emails.get("value", []),
        "chats": chats_items,
        "messages": messages,
    }
