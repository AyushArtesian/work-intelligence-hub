from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from services.graph_api import get_unread_emails_count, get_user_profile
from services.llm import generate_text
from services.rag import build_prompt, embed_query, generate_response, retrieve_relevant_docs

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    status: str
    message: str
    conversation_history: list[ChatMessage] = []


class RAGChatRequest(BaseModel):
    query: str
    user_id: str


class SourceChunk(BaseModel):
    content: str
    timestamp: str | None = None
    source: str
    sender: str | None = None


class RAGChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


def _is_unread_mail_query(text: str) -> bool:
    q = (text or "").lower()
    unread_tokens = ["unread", "not read", "pending"]
    mail_tokens = ["mail", "email", "emails", "inbox"]
    return any(t in q for t in unread_tokens) and any(t in q for t in mail_tokens)


def _resolve_token(request: Request, authorization: str | None, access_token: str | None) -> str:
    token = access_token or request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    return token


@router.post("/send")
def send_message(
    payload: ChatRequest,
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
) -> ChatResponse:
    """
    Send a chat message and get an AI response.
    """
    token = _resolve_token(request, authorization, access_token)
    
    # Get user profile for context
    user = get_user_profile(token)
    
    # Prepare conversation history
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in payload.conversation_history
    ]
    
    history_block = "\n".join([f"{m['role']}: {m['content']}" for m in history[-12:]])
    user_context = (
        f"User: {user.get('displayName', 'User')}\n"
        f"Email: {user.get('mail') or user.get('userPrincipalName') or 'N/A'}"
    )
    system_prompt = (
        "You are Work Intelligence Assistant. Provide concise, practical work guidance "
        "based on the user context and conversation history."
    )
    user_prompt = (
        f"{user_context}\n\n"
        f"Conversation History:\n{history_block or 'None'}\n\n"
        f"User Message:\n{payload.message}"
    )
    response_text = generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
    
    # Build updated conversation history
    updated_history = payload.conversation_history + [
        ChatMessage(role="user", content=payload.message),
        ChatMessage(role="assistant", content=response_text),
    ]
    
    return ChatResponse(
        status="success",
        message=response_text,
        conversation_history=updated_history,
    )


@router.post("", response_model=RAGChatResponse)
def rag_chat(
    payload: RAGChatRequest,
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    token = _resolve_token(request, authorization, access_token)
    user = get_user_profile(token)
    resolved_user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")

    if not resolved_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

    # Enforce user-level isolation for RAG data retrieval.
    if payload.user_id != resolved_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for requested user_id")

    if _is_unread_mail_query(payload.query):
        unread_count = get_unread_emails_count(token)
        return RAGChatResponse(
            answer=f"You currently have {unread_count} unread emails.",
            sources=[
                SourceChunk(
                    content="Live unread count fetched from Microsoft Graph inbox data.",
                    source="outlook",
                    timestamp=None,
                )
            ],
        )

    query_embedding = embed_query(payload.query)
    docs = retrieve_relevant_docs(query_embedding=query_embedding, user_id=resolved_user_id, top_k=5)

    if not docs:
        return RAGChatResponse(answer="No relevant information found", sources=[])

    prompt = build_prompt(payload.query, docs)
    answer = generate_response(prompt)

    source_docs: list[SourceChunk] = []
    for doc in docs[:5]:
        content = (doc.get("content") or "").strip()
        if len(content) > 280:
            content = f"{content[:277]}..."
        
        # Extract sender from metadata participants
        metadata = doc.get("metadata", {})
        participants = metadata.get("participants", [])
        sender = participants[0] if participants else None
        
        source_docs.append(
            SourceChunk(
                content=content,
                timestamp=str(doc.get("timestamp")) if doc.get("timestamp") is not None else None,
                source=doc.get("source", "unknown"),
                sender=sender,
            )
        )

    return RAGChatResponse(answer=answer, sources=source_docs)
