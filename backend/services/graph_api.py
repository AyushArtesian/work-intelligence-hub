import httpx
from fastapi import HTTPException, status

BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def _request(path: str, access_token: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    with httpx.Client(timeout=15) as client:
        response = client.get(url, headers=_get_headers(access_token), params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "graph_api_error", "status_code": response.status_code, "body": response.text},
        )
    return response.json()


def get_user_profile(access_token: str) -> dict:
    return _request("/me", access_token)


def get_emails(access_token: str) -> dict:
    return _request("/me/messages", access_token)


def get_unread_emails_count(access_token: str) -> int:
    url = f"{BASE_URL}/me/messages"
    params = {
        "$filter": "isRead eq false",
        "$count": "true",
        "$top": 1,
    }
    headers = _get_headers(access_token)
    headers["ConsistencyLevel"] = "eventual"

    with httpx.Client(timeout=15) as client:
        response = client.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "graph_api_error", "status_code": response.status_code, "body": response.text},
        )

    payload = response.json()
    count = payload.get("@odata.count")
    if isinstance(count, int):
        return count

    values = payload.get("value", [])
    if isinstance(values, list):
        return len(values)
    return 0


def get_chats(access_token: str) -> dict:
    return _request("/me/chats", access_token)


def get_chat_messages(access_token: str, chat_id: str) -> dict:
    return _request(f"/chats/{chat_id}/messages", access_token)
