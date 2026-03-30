from pydantic import BaseModel
from typing import Any, List, Optional


class TokenResponse(BaseModel):
    token_type: str
    scope: Optional[str]
    expires_in: Optional[int]
    ext_expires_in: Optional[int]
    access_token: str
    refresh_token: Optional[str]


class DataResponse(BaseModel):
    user: dict
    emails: Any
    chats: Any
    messages: Any
