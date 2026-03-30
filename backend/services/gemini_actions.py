import json
import time

import httpx
from fastapi import HTTPException, status

from utils.settings import settings

GEMINI_MODEL = "gemini-2.0-flash"
FALLBACK_MODELS = ["gemini-2.0-flash", "gemini-2.5-pro"]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MAX_API_RETRIES = 3


def _build_instruction(action_id: str) -> str:
    if action_id == "summarize":
        return (
            "You are a work assistant. Create a concise daily communication summary. "
            "Return Markdown with sections: Overview, High Priority, Key Topics, Suggested Next Steps."
        )
    if action_id == "tasks":
        return (
            "You are a task extraction assistant. Extract concrete action items from communications. "
            "Return Markdown with sections: Urgent, This Week, Later. "
            "Each item should include owner when available and deadline when available."
        )
    if action_id == "report":
        return (
            "You are an executive reporting assistant. Generate a daily work intelligence report. "
            "Return Markdown with sections: Communication Metrics, Important Signals, Risks, Recommendations."
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported action_id. Use summarize, tasks, or report.",
    )


def _safe_slice(items: list[dict], limit: int = 25) -> list[dict]:
    return items[:limit] if items else []


def generate_action_output(action_id: str, user_profile: dict, emails: list[dict], chats: list[dict], messages: list[dict]) -> str:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is missing in backend .env",
        )

    instruction = _build_instruction(action_id)

    compact_payload = {
        "user": {
            "name": user_profile.get("displayName"),
            "email": user_profile.get("mail") or user_profile.get("userPrincipalName"),
        },
        "emails": _safe_slice(
            [
                {
                    "subject": e.get("subject"),
                    "from": e.get("from"),
                    "preview": e.get("body") or e.get("bodyPreview"),
                    "received": e.get("received_datetime") or e.get("receivedDateTime"),
                }
                for e in emails
            ],
            30,
        ),
        "chats": _safe_slice(
            [
                {
                    "topic": c.get("topic"),
                    "type": c.get("type") or c.get("chatType"),
                }
                for c in chats
            ],
            20,
        ),
        "messages": _safe_slice(
            [
                {
                    "chat_id": m.get("chat_id"),
                    "from": m.get("from"),
                    "body": m.get("body"),
                    "created": m.get("created_datetime") or m.get("createdDateTime"),
                }
                for m in messages
            ],
            60,
        ),
    }

    prompt_text = (
        f"{instruction}\n\n"
        "Use only the data below. If information is missing, say so briefly instead of guessing.\n"
        "Data:\n"
        f"{json.dumps(compact_payload, default=str)}"
    )

    model_name = getattr(settings, "GEMINI_MODEL", None) or GEMINI_MODEL
    if not model_name:
        model_name = GEMINI_MODEL

    req_body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_text}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        },
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
                    "Gemini API rate limit reached after retries across configured models. "
                    "Please wait and retry, or check your Gemini quota and billing limits."
                ),
            )
        if isinstance(last_exc, httpx.HTTPStatusError) and last_exc.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Configured Gemini models were not found for generateContent. "
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

    if "candidates" in payload and payload["candidates"]:
        candidate = payload["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"]:
            text_part = candidate["content"]["parts"][0]
            return text_part.get("text", "No response text returned by Gemini.")
        return candidate.get("output", candidate.get("content", "No response returned by Gemini."))

    if "output" in payload and isinstance(payload["output"], str):
        return payload["output"]

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Gemini API returned unexpected format: {payload}",
    )

