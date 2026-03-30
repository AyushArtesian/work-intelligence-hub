import json
import re
from typing import Any

from fastapi import HTTPException, status
from groq import Groq

from utils.settings import settings


def _get_client() -> Groq:
    api_key = getattr(settings, "GROQ_API_KEY", None)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GROQ_API_KEY is missing in backend environment.",
        )
    return Groq(api_key=api_key)


def _get_model() -> str:
    return getattr(settings, "GROQ_MODEL", "qwen/qwen3-32b")


def generate_text(system_prompt: str, user_prompt: str) -> str:
    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model=_get_model(),
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = completion.choices[0].message.content if completion.choices else ""
        return (text or "").strip()
    except HTTPException:
        raise
    except Exception:
        return "I could not generate a response right now. Please try again in a moment."


def generate_json(system_prompt: str, user_prompt: str, default: Any = None) -> Any:
    json_system = (
        f"{system_prompt}\n\n"
        "Return ONLY valid JSON. Do not include markdown fences or explanations."
    )

    raw = generate_text(json_system, user_prompt)
    parsed = _extract_json(raw)
    if parsed is not None:
        return parsed

    # Retry once with stronger JSON-only instruction.
    retry_prompt = (
        f"{user_prompt}\n\n"
        "Repeat and output ONLY raw JSON with no extra text."
    )
    raw_retry = generate_text(json_system, retry_prompt)
    parsed_retry = _extract_json(raw_retry)
    if parsed_retry is not None:
        return parsed_retry

    return default


def _extract_json(text: str) -> Any | None:
    text = (text or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    first_obj = text.find("{")
    last_obj = text.rfind("}")
    if first_obj != -1 and last_obj > first_obj:
        candidate = text[first_obj : last_obj + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_arr = text.find("[")
    last_arr = text.rfind("]")
    if first_arr != -1 and last_arr > first_arr:
        candidate = text[first_arr : last_arr + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None
