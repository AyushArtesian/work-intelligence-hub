from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from services.actions import extract_tasks, generate_daily_report, summarize_emails
from services.agent import run_agent
from services.graph_api import get_user_profile
from utils.settings import settings

router = APIRouter(prefix="/actions", tags=["actions"])
agent_router = APIRouter(tags=["agent"])


class ActionRunRequest(BaseModel):
    action_id: str


class AgentRequest(BaseModel):
    query: str
    user_id: str


def _resolve_token(request: Request, authorization: str | None, access_token: str | None) -> str:
    token = access_token or request.cookies.get("work_intel_access_token")
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")
    return token


@router.get("/models")
async def list_models():
    model = getattr(settings, "GROQ_MODEL", "qwen/qwen3-32b")
    return {
        "provider": "groq",
        "model": model,
        "status": "configured" if getattr(settings, "GROQ_API_KEY", None) else "missing_api_key",
    }


@router.post("/run")
def run_action(
    payload: ActionRunRequest,
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    token = _resolve_token(request, authorization, access_token)

    user = get_user_profile(token)
    user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

    if payload.action_id == "summarize":
        output = summarize_emails(user_id)
    elif payload.action_id == "tasks":
        output = extract_tasks(user_id)
    elif payload.action_id == "report":
        output = generate_daily_report(user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported action_id. Use summarize, tasks, or report.",
        )

    return {
        "status": "success",
        "action_id": payload.action_id,
        "result": output,
    }


@agent_router.post("/agent")
def run_agent_route(
    payload: AgentRequest,
    request: Request,
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
):
    token = _resolve_token(request, authorization, access_token)
    user = get_user_profile(token)
    resolved_user_id = user.get("mail") or user.get("userPrincipalName") or user.get("id")

    if not resolved_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to resolve user id")

    if payload.user_id != resolved_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for requested user_id")

    result = run_agent(query=payload.query, user_id=resolved_user_id)
    return result
