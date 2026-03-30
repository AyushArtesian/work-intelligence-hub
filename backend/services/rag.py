from typing import Any

from bson import ObjectId
from fastapi import HTTPException, status

from db.mongodb import get_messages_collection
from services.embedding import generate_embedding
from services.llm import generate_text
from services.vector_store import add_embedding, search_similar

DEFAULT_TOP_K = 5
MAX_CONTEXT_CHARS = 6000


def embed_query(query: str) -> list[float]:
    return generate_embedding(query)


def retrieve_relevant_docs(query_embedding: list[float], user_id: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    collection = get_messages_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    matches = search_similar(query_embedding, top_k=top_k)
    if not matches:
        _hydrate_vectors_for_user(collection, user_id)
        matches = search_similar(query_embedding, top_k=top_k)
    if not matches:
        return []

    docs_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for item in matches:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue
        ordered_ids.append(doc_id)
        try:
            docs_by_id[doc_id] = collection.find_one({"_id": ObjectId(doc_id), "user_id": user_id}) or {}
        except Exception:
            docs_by_id[doc_id] = {}

    relevant_docs: list[dict[str, Any]] = []
    for item in matches:
        doc_id = item.get("doc_id")
        if not doc_id:
            continue
        doc = docs_by_id.get(doc_id)
        if not doc:
            continue
        relevant_docs.append(
            {
                "_id": str(doc.get("_id")),
                "content": doc.get("content", ""),
                "source": doc.get("source", "unknown"),
                "timestamp": doc.get("timestamp"),
                "metadata": doc.get("metadata", {}),
                "score": item.get("score", 0.0),
            }
        )

    return relevant_docs


def _hydrate_vectors_for_user(collection, user_id: str) -> None:
    cursor = collection.find({"user_id": user_id}, {"_id": 1, "content": 1}).limit(500)
    for doc in cursor:
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        embedding = generate_embedding(content)
        add_embedding(str(doc.get("_id")), embedding)


def build_prompt(query: str, context_docs: list[dict[str, Any]]) -> str:
    context_chunks: list[str] = []
    total_chars = 0

    for idx, doc in enumerate(context_docs, start=1):
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        source = doc.get("source", "unknown")
        timestamp = doc.get("timestamp")
        chunk = f"[{idx}] Source: {source}; Timestamp: {timestamp}\n{content}"

        if total_chars + len(chunk) > MAX_CONTEXT_CHARS:
            break

        context_chunks.append(chunk)
        total_chars += len(chunk)

    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant context available."

    return (
        "You are an AI assistant helping a user understand their work data.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question:\n{query}\n\n"
        "Instructions:\n"
        "- Answer ONLY from the context.\n"
        "- If not found, say exactly: I don't have enough information.\n"
        "- Be clear and structured.\n"
        "- Extract actionable insights if possible.\n"
    )


def generate_response(prompt: str) -> str:
    system_prompt = (
        "You are an AI assistant helping users understand work data from emails and chats. "
        "Answer only from provided context. If context is insufficient, say: I don't have enough information."
    )
    response = generate_text(system_prompt=system_prompt, user_prompt=prompt)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate LLM response.",
        )
    return response
