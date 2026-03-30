import json
from typing import Any

from fastapi import HTTPException, status

from db.mongodb import get_messages_collection
from services.llm import generate_json, generate_text

MAX_COMBINED_CHARS = 9000


def summarize_emails(user_id: str) -> dict[str, Any]:
    collection = get_messages_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    docs = list(
        collection.find({"user_id": user_id, "source": "outlook"}, {"content": 1, "timestamp": 1, "metadata": 1})
        .sort("timestamp", -1)
        .limit(40)
    )
    if not docs:
        return {
            "action": "summarize_emails",
            "status": "no_data",
            "summary": "No email data found for this user.",
            "items": [],
        }

    combined = _join_docs_for_prompt(docs)
    system_prompt = "You are a concise work intelligence summarization assistant."
    user_prompt = (
        "Summarize the following emails clearly and concisely.\n"
        "Return sections: Overview, Highlights, Risks, Next Steps.\n\n"
        f"Content:\n{combined}"
    )

    text_summary = generate_text(system_prompt=system_prompt, user_prompt=user_prompt)
    return {
        "action": "summarize_emails",
        "status": "success",
        "email_count": len(docs),
        "summary": text_summary,
    }


def extract_tasks(user_id: str) -> dict[str, Any]:
    collection = get_messages_collection()
    if collection is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    docs = list(
        collection.find({"user_id": user_id, "source": {"$in": ["teams", "outlook"]}}, {"content": 1, "timestamp": 1, "source": 1, "metadata": 1})
        .sort("timestamp", -1)
        .limit(80)
    )
    if not docs:
        return {
            "action": "extract_tasks",
            "status": "no_data",
            "tasks": [],
        }

    combined = _join_docs_for_prompt(docs)
    system_prompt = "You extract actionable tasks from work communications."
    user_prompt = (
        "Extract actionable tasks from the following content.\n"
        "Return JSON array:\n"
        "[\n"
        '  {"task": "...", "deadline": "...", "context": "..."}\n'
        "]\n"
        "If no tasks exist, return [].\n\n"
        f"Content:\n{combined}"
    )

    parsed = generate_json(system_prompt=system_prompt, user_prompt=user_prompt, default=[])
    tasks = parsed if isinstance(parsed, list) else []

    normalized_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        normalized_tasks.append(
            {
                "task": str(task.get("task", "")).strip(),
                "deadline": _none_if_empty(task.get("deadline")),
                "context": _none_if_empty(task.get("context")),
                "source": _guess_source_from_context(task.get("context")),
            }
        )

    return {
        "action": "extract_tasks",
        "status": "success",
        "task_count": len(normalized_tasks),
        "tasks": normalized_tasks,
    }


def generate_daily_report(user_id: str) -> dict[str, Any]:
    summary_result = summarize_emails(user_id)
    tasks_result = extract_tasks(user_id)

    summary_json = json.dumps(summary_result.get("summary", {}), default=str)
    tasks_json = json.dumps(tasks_result.get("tasks", []), default=str)

    system_prompt = "You create structured daily work intelligence reports."
    user_prompt = (
        "Create a concise daily work intelligence report from the inputs below.\n"
        "Return JSON only with keys: executive_summary, priorities, blockers, recommendations.\n\n"
        f"Email Summary Input: {summary_json}\n"
        f"Task Input: {tasks_json}\n"
    )

    report = generate_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        default={"executive_summary": "", "priorities": [], "blockers": [], "recommendations": []},
    )

    return {
        "action": "generate_report",
        "status": "success",
        "summary": summary_result.get("summary", {}),
        "tasks": tasks_result.get("tasks", []),
        "report": report,
    }


def _join_docs_for_prompt(docs: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    total = 0
    for idx, doc in enumerate(docs, start=1):
        source = doc.get("source", "unknown")
        timestamp = doc.get("timestamp")
        content = str(doc.get("content", "")).strip()
        if not content:
            continue

        block = f"[{idx}] source={source} timestamp={timestamp}\\n{content}"
        if total + len(block) > MAX_COMBINED_CHARS:
            break
        chunks.append(block)
        total += len(block)

    return "\n\n".join(chunks)


def _llm_json(prompt: str, default: Any) -> Any:
    return generate_json(system_prompt="Return strictly valid JSON.", user_prompt=prompt, default=default)
def _none_if_empty(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _guess_source_from_context(value: Any) -> str:
    context = str(value or "").lower()
    if "email" in context or "outlook" in context:
        return "outlook"
    if "teams" in context or "chat" in context:
        return "teams"
    return "unknown"
