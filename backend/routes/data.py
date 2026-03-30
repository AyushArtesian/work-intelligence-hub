from fastapi import APIRouter, Header, Query, HTTPException, status, Request

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
    request: Request, authorization: str | None = Header(None), access_token: str | None = Query(None)
):
    """Fetches user profile, emails, chats, and chat messages from Microsoft Graph."""
    # Get token from query param first, then cookie, then Authorization header
    token = access_token
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token:
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


@router.post("/sync")
def sync_data(request: Request, authorization: str | None = Header(None), access_token: str | None = Query(None)):
    """Syncs emails, chats, and messages from Microsoft Graph and stores them in MongoDB."""
    # Get token from cookie first, then header, then query
    token = access_token
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token:
        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )

    try:
        # Fetch data from Graph API
        user = get_user_profile(token)
        user_id = user.get("id") or user.get("userPrincipalName")
        user_email = user.get("mail") or user.get("userPrincipalName")

        emails_data = get_emails(token)
        chats_data = get_chats(token)
        
        emails_items = emails_data.get("value", [])
        chats_items = chats_data.get("value", [])
        
        # Connect to DB
        db = get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )
        
        # Store emails with upsert (avoid duplicates by id)
        emails_synced = 0
        for email in emails_items:
            try:
                db.emails.update_one(
                    {"_id": email.get("id")},
                    {
                        "$set": {
                            "_id": email.get("id"),
                            "user_id": user_id,
                            "user_email": user_email,
                            "subject": email.get("subject"),
                            "from": email.get("from"),
                            "to": email.get("toRecipients"),
                            "body": email.get("bodyPreview"),
                            "received_datetime": email.get("receivedDateTime"),
                            "is_read": email.get("isRead"),
                            "raw_data": email,
                        }
                    },
                    upsert=True,
                )
                emails_synced += 1
            except Exception as exc:
                print(f"[WARNING] Failed to sync email {email.get('id')}: {exc}")
        
        # Store chats and messages
        chats_synced = 0
        messages_synced = 0
        
        for chat in chats_items[:10]:  # limit to first 10 chats for now
            chat_id = chat.get("id")
            if not chat_id:
                continue
            
            try:
                # Store chat metadata
                db.chats.update_one(
                    {"_id": chat_id},
                    {
                        "$set": {
                            "_id": chat_id,
                            "user_id": user_id,
                            "topic": chat.get("topic"),
                            "type": chat.get("chatType"),
                            "raw_data": chat,
                        }
                    },
                    upsert=True,
                )
                chats_synced += 1
                
                # Fetch and store messages from this chat
                try:
                    chat_messages_data = get_chat_messages(token, chat_id)
                    chat_messages = chat_messages_data.get("value", [])
                    
                    for msg in chat_messages:
                        msg_id = msg.get("id")
                        if msg_id:
                            db.messages.update_one(
                                {"_id": msg_id},
                                {
                                    "$set": {
                                        "_id": msg_id,
                                        "user_id": user_id,
                                        "chat_id": chat_id,
                                        "from": msg.get("from"),
                                        "body": msg.get("body"),
                                        "created_datetime": msg.get("createdDateTime"),
                                        "raw_data": msg,
                                    }
                                },
                                upsert=True,
                            )
                            messages_synced += 1
                except Exception as exc:
                    print(f"[WARNING] Failed to sync messages for chat {chat_id}: {exc}")
            
            except Exception as exc:
                print(f"[WARNING] Failed to sync chat {chat_id}: {exc}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "user_email": user_email,
            "emails_synced": emails_synced,
            "chats_synced": chats_synced,
            "messages_synced": messages_synced,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Sync failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(exc)}",
        )
