from typing import Any

from services.actions import extract_tasks, generate_daily_report, summarize_emails
from services.llm import generate_json
from services.rag import build_prompt, embed_query, generate_response, retrieve_relevant_docs

VALID_ACTIONS = {"summarize_emails", "extract_tasks", "generate_report", "general_question"}


def detect_action(query: str) -> str:
    system_prompt = "You classify work-assistant intents."
    user_prompt = (
        "Classify the user query into one of the following:\n"
        "- summarize_emails\n"
        "- extract_tasks\n"
        "- generate_report\n"
        "- general_question\n\n"
        "Return ONLY JSON:\n"
        '{"action":"..."}\n\n'
        f"Query: {query}"
    )

    parsed = generate_json(system_prompt=system_prompt, user_prompt=user_prompt, default={"action": "general_question"})
    action = (parsed or {}).get("action") if isinstance(parsed, dict) else None
    if isinstance(action, str) and action in VALID_ACTIONS:
        return action

    return _heuristic_action(query)


def run_agent(query: str, user_id: str) -> dict[str, Any]:
    action = detect_action(query)

    if action == "summarize_emails":
        return {"type": "action", "action": action, "result": summarize_emails(user_id)}

    if action == "extract_tasks":
        return {"type": "action", "action": action, "result": extract_tasks(user_id)}

    if action == "generate_report":
        return {"type": "action", "action": action, "result": generate_daily_report(user_id)}

    query_embedding = embed_query(query)
    docs = retrieve_relevant_docs(query_embedding=query_embedding, user_id=user_id, top_k=5)
    if not docs:
        return {
            "type": "chat",
            "action": "general_question",
            "result": {"answer": "No relevant information found", "sources": []},
        }

    prompt = build_prompt(query, docs)
    answer = generate_response(prompt)

    sources = []
    for doc in docs[:5]:
        content = (doc.get("content") or "").strip()
        if len(content) > 280:
            content = f"{content[:277]}..."
        sources.append(
            {
                "content": content,
                "timestamp": str(doc.get("timestamp")) if doc.get("timestamp") is not None else None,
                "source": doc.get("source", "unknown"),
            }
        )

    return {
        "type": "chat",
        "action": "general_question",
        "result": {"answer": answer, "sources": sources},
    }


def _heuristic_action(query: str) -> str:
    q = (query or "").lower()
    if any(k in q for k in ["summarize", "summary", "email summary", "inbox summary"]):
        return "summarize_emails"
    if any(k in q for k in ["task", "todo", "to-do", "deadline", "action item"]):
        return "extract_tasks"
    if any(k in q for k in ["daily report", "report", "briefing", "status report"]):
        return "generate_report"
    return "general_question"
