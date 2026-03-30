import hashlib
import math
from typing import List

import httpx
from fastapi import HTTPException, status

from utils.settings import settings

OPENAI_EMBEDDING_URL = "https://api.openai.com/v1/embeddings"
GEMINI_EMBEDDING_BASE = "https://generativelanguage.googleapis.com/v1beta"
FALLBACK_DIMENSION = 256


def generate_embedding(text: str) -> List[float]:
    normalized = (text or "").strip()
    if not normalized:
        return [0.0] * FALLBACK_DIMENSION

    if getattr(settings, "OPENAI_API_KEY", None):
        return _embed_openai(normalized)

    if getattr(settings, "GEMINI_API_KEY", None):
        return _embed_gemini(normalized)

    return _embed_local_fallback(normalized)


def _embed_openai(text: str) -> List[float]:
    model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"model": model, "input": text}

    try:
        response = httpx.post(OPENAI_EMBEDDING_URL, headers=headers, json=body, timeout=45.0)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        if not data:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI embedding response was empty")
        return data[0]["embedding"]
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI embedding failed with status {exc.response.status_code}: {exc.response.text[:300]}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenAI embedding request failed: {exc}")


def _embed_gemini(text: str) -> List[float]:
    model = getattr(settings, "GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    url = f"{GEMINI_EMBEDDING_BASE}/models/{model}:embedContent?key={settings.GEMINI_API_KEY}"
    body = {
        "content": {
            "parts": [{"text": text}],
        }
    }

    try:
        response = httpx.post(url, json=body, timeout=45.0)
        response.raise_for_status()
        payload = response.json()
        embedding = payload.get("embedding", {}).get("values")
        if not embedding:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gemini embedding response was empty")
        return embedding
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini embedding failed with status {exc.response.status_code}: {exc.response.text[:300]}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gemini embedding request failed: {exc}")


def _embed_local_fallback(text: str) -> List[float]:
    # Deterministic fallback for local/dev mode when no embedding provider is configured.
    vec = [0.0] * FALLBACK_DIMENSION
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % FALLBACK_DIMENSION
        sign = -1.0 if int(digest[8:9], 16) % 2 else 1.0
        vec[idx] += sign

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]
