import hashlib
import logging
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

from pymongo.errors import DuplicateKeyError

from db.mongodb import get_messages_collection
from services.embedding import generate_embedding
from services.graph_api import get_chat_messages, get_chats, get_emails, get_user_profile
from services.vector_store import add_embedding

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    stripped = TAG_RE.sub(" ", text)
    normalized = WS_RE.sub(" ", unescape(stripped)).strip()
    return normalized


def chunk_text(text: str, chunk_size: int = 300) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    current = 0
    while current < len(text):
        end = min(len(text), current + chunk_size)
        if end < len(text):
            split = text.rfind(" ", current, end)
            if split > current:
                end = split
        chunks.append(text[current:end].strip())
        current = end
        while current < len(text) and text[current] == " ":
            current += 1
    return [c for c in chunks if c]


def process_messages(raw_data: dict[str, Any], user_id: str) -> list[dict[str, Any]]:
    processed: list[dict[str, Any]] = []

    emails = raw_data.get("emails", []) or []
    chats = {c.get("id"): c for c in (raw_data.get("chats", []) or []) if c.get("id")}
    messages = raw_data.get("messages", []) or []

    for email in emails:
        raw_body = _extract_email_body(email)
        content = clean_text(raw_body)
        if not content:
            continue

        chunks = chunk_text(content)
        participants = _email_participants(email)
        ts = _parse_timestamp(email.get("receivedDateTime"))

        for chunk_idx, chunk in enumerate(chunks):
            doc = {
                "user_id": user_id,
                "source": "outlook",
                "content": chunk,
                "timestamp": ts,
                "chat_id": None,
                "message_id": email.get("id"),
                "metadata": {
                    "team": None,
                    "participants": participants,
                    "subject": email.get("subject"),
                    "chunk_index": chunk_idx,
                    "chunk_total": len(chunks),
                },
            }
            doc["content_hash"] = _content_hash(doc)
            processed.append(doc)

    for msg in messages:
        raw_body = _extract_chat_body(msg)
        content = clean_text(raw_body)
        if not content:
            continue

        chunks = chunk_text(content)
        chat_id = msg.get("chat_id")
        chat = chats.get(chat_id, {})
        participants = _message_participants(msg)
        ts = _parse_timestamp(msg.get("createdDateTime"))

        for chunk_idx, chunk in enumerate(chunks):
            doc = {
                "user_id": user_id,
                "source": "teams",
                "content": chunk,
                "timestamp": ts,
                "chat_id": chat_id,
                "message_id": msg.get("id"),
                "metadata": {
                    "team": chat.get("topic") or chat.get("chatType"),
                    "participants": participants,
                    "chunk_index": chunk_idx,
                    "chunk_total": len(chunks),
                },
            }
            doc["content_hash"] = _content_hash(doc)
            processed.append(doc)

    return processed


def fetch_and_process(user_id: str | None, access_token: str, since: str | None = None) -> dict[str, Any]:
    """
    Fetches and processes emails/chats from Microsoft Graph.
    If 'since' is provided, only fetches data newer than that timestamp (incremental sync).
    """
    user_profile = get_user_profile(access_token)
    resolved_user_id = user_id or user_profile.get("mail") or user_profile.get("userPrincipalName") or user_profile.get("id")
    if not resolved_user_id:
        raise ValueError("Unable to resolve user id from profile")

    # Fetch emails (with optional timestamp filter for incremental sync)
    emails = get_emails(access_token, since=since).get("value", [])
    chats = get_chats(access_token).get("value", [])

    all_messages: list[dict[str, Any]] = []
    for chat in chats[:15]:
        chat_id = chat.get("id")
        if not chat_id:
            continue
        # Fetch messages with optional timestamp filter for incremental sync
        msg_payload = get_chat_messages(access_token, chat_id, since=since).get("value", [])
        for msg in msg_payload:
            msg["chat_id"] = chat_id
            all_messages.append(msg)

    raw_data = {"emails": emails, "chats": chats, "messages": all_messages}
    return process_and_store_raw_data(raw_data=raw_data, user_id=resolved_user_id)


def process_and_store_raw_data(raw_data: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Process already-fetched raw payload and persist it into MongoDB/vector index."""
    processed_docs = process_messages(raw_data=raw_data, user_id=user_id)

    messages_collection = get_messages_collection()
    if messages_collection is None:
        raise RuntimeError("MongoDB is not available")

    saved = 0
    indexed = 0

    for doc in processed_docs:
        identity_filter = _document_identity_filter(doc)
        update = {"$setOnInsert": doc}
        try:
            result = messages_collection.update_one(identity_filter, update, upsert=True)
        except DuplicateKeyError:
            # Another matching record already exists (legacy index/race); treat as existing doc.
            result = None

        if result is not None and result.upserted_id is not None:
            doc_id = str(result.upserted_id)
            saved += 1
        else:
            existing = messages_collection.find_one(identity_filter, {"_id": 1})
            if not existing:
                continue
            doc_id = str(existing["_id"])

        try:
            embedding = generate_embedding(doc["content"])
            add_embedding(doc_id=doc_id, embedding=embedding)
            indexed += 1
        except Exception as exc:
            logger.warning(
                "Embedding/indexing failed for doc_id=%s user=%s: %s",
                doc_id,
                user_id,
                exc,
            )

    logger.info("Data process completed user=%s saved=%s indexed=%s", user_id, saved, indexed)

    return {
        "status": "processed",
        "documents_saved": saved,
        "documents_indexed": indexed,
        "user_id": user_id,
    }


def _extract_email_body(email: dict[str, Any]) -> str:
    body = email.get("body")
    if isinstance(body, dict):
        return body.get("content") or email.get("bodyPreview") or ""
    return email.get("bodyPreview") or ""


def _extract_chat_body(message: dict[str, Any]) -> str:
    body = message.get("body")
    if isinstance(body, dict):
        return body.get("content") or ""
    return str(body or "")


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        iso = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(iso)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _email_participants(email: dict[str, Any]) -> list[str]:
    participants: list[str] = []

    sender = (email.get("from") or {}).get("emailAddress") or {}
    if sender.get("address"):
        participants.append(sender["address"])

    for recipient in email.get("toRecipients", []) or []:
        address = (recipient.get("emailAddress") or {}).get("address")
        if address:
            participants.append(address)

    return sorted(set(participants))


def _message_participants(message: dict[str, Any]) -> list[str]:
    sender = (((message.get("from") or {}).get("user") or {}).get("displayName"))
    return [sender] if sender else []


def _content_hash(doc: dict[str, Any]) -> str:
    stable = "|".join(
        [
            str(doc.get("user_id") or ""),
            str(doc.get("source") or ""),
            str(doc.get("message_id") or ""),
            str(doc.get("chat_id") or ""),
            str(doc.get("metadata", {}).get("chunk_index") or 0),
            str(doc.get("content") or ""),
        ]
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _document_identity_filter(doc: dict[str, Any]) -> dict[str, Any]:
    if doc.get("message_id"):
        return {
            "user_id": doc.get("user_id"),
            "source": doc.get("source"),
            "message_id": doc.get("message_id"),
            "metadata.chunk_index": doc.get("metadata", {}).get("chunk_index", 0),
        }
    return {"content_hash": doc["content_hash"]}
