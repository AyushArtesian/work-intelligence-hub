import logging

from fastapi import APIRouter, Body, Header, Query, HTTPException, status, Request
from pydantic import BaseModel

from services.graph_api import get_user_profile, get_emails, get_chats, get_chat_messages
from services.processor import fetch_and_process
from models.response_models import DataResponse
from utils.mongodb import get_db

router = APIRouter(prefix="/data", tags=["data"])
logger = logging.getLogger(__name__)


class DataProcessRequest(BaseModel):
    access_token: str | None = None


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


@router.post("/fetch", response_model=DataResponse)
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


@router.get("/fetch", response_model=DataResponse)
def fetch_data_get(
    request: Request, authorization: str | None = Header(None), access_token: str | None = Query(None)
):
    # Backward-compatible alias for older clients still issuing GET.
    return fetch_data(request=request, authorization=authorization, access_token=access_token)


@router.post("/sync")
def sync_data(request: Request, authorization: str | None = Header(None), access_token: str | None = Query(None)):
    """
    Syncs data from Microsoft Graph: fetches emails/chats, processes them, chunks them,
    generates embeddings, and indexes them for RAG. Complete end-to-end pipeline.
    """
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
        user = get_user_profile(token)
        user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

        # Run the complete fetch+process pipeline
        result = fetch_and_process(user_id=user_id, access_token=token)
        
        return {
            "status": "success",
            "user_id": user_id,
            "documents_saved": result.get("documents_saved", 0),
            "documents_indexed": result.get("documents_indexed", 0),
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Sync failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(exc)}",
        )


@router.post("/process")
def process_data(
    request: Request,
    payload: DataProcessRequest | None = Body(default=None),
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    token = access_token or (payload.access_token if payload else None)
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token:
        token = _resolve_access_token(authorization, access_token)

    user = get_user_profile(token)
    user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

    try:
        result = fetch_and_process(user_id=user_id, access_token=token)
        return {
            "status": "processed",
            "documents_saved": result.get("documents_saved", 0),
            "documents_indexed": result.get("documents_indexed", 0),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Data processing failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data processing failed: {exc}")
