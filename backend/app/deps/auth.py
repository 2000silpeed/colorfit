from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.jwt import verify_access_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID:
    if cred is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    user_id = verify_access_token(cred.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
    return user_id


async def get_optional_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID | None:
    if cred is None:
        return None
    return verify_access_token(cred.credentials)
