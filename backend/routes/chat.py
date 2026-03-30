from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from services.gemini_chat import send_chat_message
from services.graph_api import get_user_profile
from utils.settings import settings

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
    
    # Get response from Gemini
    response_text = send_chat_message(
        user_message=payload.message,
        conversation_history=history,
        user_context=user
    )
    
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
