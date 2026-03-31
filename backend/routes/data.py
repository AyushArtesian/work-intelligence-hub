import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Header, Query, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel

from services.graph_api import get_user_profile, get_emails, get_chats, get_chat_messages
from services.processor import fetch_and_process, process_and_store_raw_data
from services.llm import generate_json
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
    request: Request, background_tasks: BackgroundTasks, authorization: str | None = Header(None), access_token: str | None = Query(None)
):
    """
    Fetches latest user profile, emails, chats, and chat messages from Microsoft Graph.
    Returns data ordered by most recent first (latest data).
    Persistence (storage/indexing) runs in background to avoid blocking response.
    """
    # Get token from query param first, then cookie, then Authorization header
    token = access_token
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token:
        token = _resolve_access_token(authorization, access_token)

    user = get_user_profile(token)
    # Fetch up to 100 latest emails (ordered by receivedDateTime desc)
    emails = get_emails(token, top=100)
    # Fetch up to 50 latest chats
    chats = get_chats(token, top=50)

    # Fetch messages from ALL available chats (not just first 2)
    # This ensures we get messages from all teams conversations
    chats_items = chats.get("value", [])
    
    messages = []
    flat_messages = []
    for chat in chats_items:
        chat_id = chat.get("id")
        if chat_id:
            try:
                # Fetch up to 50 latest messages per chat (Teams API max is 50, ordered by createdDateTime desc)
                chat_messages = get_chat_messages(token, chat_id, top=50)
                grouped_messages = chat_messages.get("value", [])
                messages.append({"chat_id": chat_id, "messages": grouped_messages})

                for msg in grouped_messages:
                    if isinstance(msg, dict):
                        msg_with_chat = dict(msg)
                        msg_with_chat["chat_id"] = chat_id
                        flat_messages.append(msg_with_chat)
            except Exception as exc:
                logger.warning(f"Failed to fetch messages from chat {chat_id}: {exc}")
                continue

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
                    "total_messages": sum(len(m.get("messages", [])) for m in messages),
                }
            )
        except Exception as exc:
            # do not fail the endpoint for DB issues; log for developer
            logger.warning(f"Unable to write fetch_history: {exc}")

    user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
    if user_id:
        # Schedule persistence in background so fetch response returns immediately
        background_tasks.add_task(
            process_and_store_raw_data,
            raw_data={
                "emails": emails.get("value", []),
                "chats": chats_items,
                "messages": flat_messages,
            },
            user_id=user_id,
        )

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
    Syncs data from Microsoft Graph: fetches ONLY NEW emails/chats, processes them, chunks them,
    generates embeddings, and indexes them for RAG. Incremental sync based on last_sync_timestamp.
    """
    # Token resolution: query param → cookie → Authorization header
    token = access_token
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token. Ensure you're logged in. Provide in Authorization header, cookie, or access_token query param.",
        )

    try:
        user = get_user_profile(token)
        user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

        # Get user's last sync timestamp from MongoDB
        db = get_db()
        last_sync_doc = None
        since_timestamp = None
        if db is not None:
            last_sync_doc = db.users.find_one({"user_id": user_id})
            if last_sync_doc and last_sync_doc.get("last_sync_timestamp"):
                since_timestamp = last_sync_doc["last_sync_timestamp"]
        
        # Run the complete fetch+process pipeline with incremental filtering
        result = fetch_and_process(user_id=user_id, access_token=token, since=since_timestamp)
        
        # Update user's last_sync_timestamp
        sync_timestamp = __import__("datetime").datetime.utcnow().isoformat()
        if db is not None:
            try:
                db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_sync_timestamp": sync_timestamp}},
                    upsert=True
                )
            except Exception as exc:
                logger.warning(f"Failed to update last_sync_timestamp: {exc}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "documents_saved": result.get("documents_saved", 0),
            "documents_indexed": result.get("documents_indexed", 0),
            "is_incremental": since_timestamp is not None,
            "last_sync_timestamp": sync_timestamp,
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
    # Token resolution: query param → body payload → cookie → Authorization header
    token = access_token or (payload.access_token if payload else None)
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token. Ensure you're logged in. Provide in Authorization header, cookie, or access_token query param.",
        )

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


@router.post("/insights")
def generate_insights(
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    """
    Generates AI-powered insights from user's messages.
    Returns: Weekly summary, key decisions, risks identified, and trends.
    """
    # Token resolution
    token = access_token
    if not token:
        token = request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token.",
        )

    try:
        user = get_user_profile(token)
        user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

        # Get messages from past 7 days
        db = get_db()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database unavailable",
            )

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        messages = list(db.messages.find(
            {
                "user_id": user_id,
                "timestamp": {"$gte": seven_days_ago}
            },
            {"content": 1, "source": 1, "timestamp": 1, "metadata": 1}
        ).limit(200))

        if not messages:
            return {
                "weekly_summary": [
                    "No messages found for the past 7 days.",
                    "Sync your data to generate insights."
                ],
                "key_decisions": [],
                "risks": [],
                "trends": []
            }

        # Prepare message content for analysis
        message_texts = [m.get("content", "") for m in messages]
        combined_content = "\n".join(message_texts[:100])  # Limit to prevent token overload

        system_prompt = (
            "You are an AI workplace intelligence analyst. Analyze communication data and generate "
            "structured insights about work patterns, decisions, risks, and trends. "
            "Return valid JSON only, no markdown or extra text."
        )

        user_prompt = f"""Analyze these recent messages and generate structured insights.
Return a JSON object with exactly these fields:
- weekly_summary: array of 3-4 strings about overall activity patterns
- key_decisions: array of 3-4 strings about important decisions made
- risks: array of 2-3 strings about potential risks or concerns
- trends: array of 2-3 strings about notable trends or patterns

Messages to analyze:
{combined_content[:2000]}

Return ONLY valid JSON."""

        insights = generate_json(system_prompt, user_prompt, default={
            "weekly_summary": [],
            "key_decisions": [],
            "risks": [],
            "trends": []
        })

        # Ensure all fields exist
        return {
            "weekly_summary": insights.get("weekly_summary", []),
            "key_decisions": insights.get("key_decisions", []),
            "risks": insights.get("risks", []),
            "trends": insights.get("trends", [])
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Insights generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights generation failed: {str(exc)}"
        )
