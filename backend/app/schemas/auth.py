from __future__ import annotations

from pydantic import BaseModel


class OAuthCallbackRequest(BaseModel):
    code: str
    guest_user_id: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    is_new_user: bool
