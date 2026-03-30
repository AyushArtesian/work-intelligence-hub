import json
import time

import httpx
from fastapi import HTTPException, status

from utils.settings import settings

GEMINI_MODEL = "gemini-2.0-flash"
FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.5-pro"]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MAX_API_RETRIES = 3

SYSTEM_PROMPT = (
    "You are Work Intelligence, a helpful AI assistant for workplace productivity and communication analysis. "
    "You help users understand their emails, chats, and tasks. Keep responses concise, actionable, and relevant. "
    "When discussing work items, offer specific next steps and prioritization. "
    "Always be professional, encouraging, and focused on productivity."
)


def send_chat_message(user_message: str, conversation_history: list[dict], user_context: dict | None = None) -> str:
    """
    Send a chat message to Gemini and get a response.
    
    Args:
        user_message: The user's message
        conversation_history: List of previous messages with role and content
        user_context: Optional user context (profile, email count, etc.)
    
    Returns:
        Assistant response text
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is missing in backend .env",
        )

    # Build context from user profile if provided
    context_text = ""
    if user_context:
        context_text = (
            f"User: {user_context.get('displayName', 'User')}\n"
            f"Email: {user_context.get('mail') or user_context.get('userPrincipalName', 'N/A')}\n"
        )

    # Prepare messages for API
    contents = []
    
    # Add conversation history
    for msg in conversation_history:
        contents.append({
            "role": msg.get("role", "user"),
            "parts": [{"text": msg.get("content", "")}]
        })
    
    # Add current user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    req_body = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        },
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        }
    }

    def call_model(name: str):
        url = f"{GEMINI_API_BASE}/models/{name}:generateContent?key={settings.GEMINI_API_KEY}"
        for attempt in range(MAX_API_RETRIES + 1):
            try:
                response = httpx.post(url, json=req_body, timeout=60.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                is_retryable = status_code in {408, 429, 500, 502, 503, 504}
                if not is_retryable or attempt >= MAX_API_RETRIES:
                    raise
                retry_after = exc.response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = min(float(retry_after), 15.0)
                else:
                    delay = min(1.5 * (2**attempt), 15.0)
                time.sleep(delay)
            except httpx.RequestError:
                if attempt >= MAX_API_RETRIES:
                    raise
                delay = min(1.5 * (2**attempt), 15.0)
                time.sleep(delay)

    model_name = getattr(settings, "GEMINI_MODEL", None) or GEMINI_MODEL
    if not model_name:
        model_name = GEMINI_MODEL

    models_to_try = [model_name] + [m for m in FALLBACK_MODELS if m != model_name]
    last_exc = None
    
    for name in models_to_try:
        try:
            payload = call_model(name)
            model_name = name
            break
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code == 404:
                continue
            if exc.response.status_code == 429:
                continue
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"Gemini request failed for model '{name}' with status {exc.response.status_code}. "
                    f"Response: {exc.response.text[:500]}"
                ),
            )
        except httpx.RequestError as exc:
            last_exc = exc
            continue
    else:
        if isinstance(last_exc, httpx.HTTPStatusError) and last_exc.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Gemini API rate limit reached. "
                    "Please wait and retry, or check your Gemini quota and billing limits."
                ),
            )
        if isinstance(last_exc, httpx.HTTPStatusError) and last_exc.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Configured Gemini models were not found. "
                    f"Tried: {models_to_try}."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to get a response from Gemini after retries and model fallbacks. "
                f"Tried: {models_to_try}."
            ),
        )

    # Extract response text
    if "candidates" in payload and payload["candidates"]:
        candidate = payload["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"]:
            text_part = candidate["content"]["parts"][0]
            return text_part.get("text", "I encountered an issue generating a response. Please try again.")
        return candidate.get("output", "No response text returned by Gemini.")

    if "output" in payload and isinstance(payload["output"], str):
        return payload["output"]

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Gemini API returned unexpected format: {payload}",
    )
