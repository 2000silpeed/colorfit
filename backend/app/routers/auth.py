"""Auth API — 카카오/구글 소셜 로그인 + 게스트→로그인 전환"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import OAuthCallbackRequest, AuthTokenResponse
from app.services.jwt import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_URL = "https://kapi.kakao.com/v2/user/me"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


async def _get_kakao_user(code: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        token_data: dict[str, str] = {
            "grant_type": "authorization_code",
            "client_id": settings.kakao_client_id,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if settings.kakao_client_secret:
            token_data["client_secret"] = settings.kakao_client_secret
        token_resp = await client.post(KAKAO_TOKEN_URL, data=token_data)
        if token_resp.status_code != 200:
            logger.error("kakao token error: %s", token_resp.text)
            raise HTTPException(status_code=401, detail="카카오 인증에 실패했습니다")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="카카오 토큰 응답이 올바르지 않습니다")

        user_resp = await client.get(
            KAKAO_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="카카오 사용자 정보를 가져올 수 없습니다")

        data = user_resp.json()
        kakao_account = data.get("kakao_account", {})
        return {
            "email": kakao_account.get("email"),
            "provider": "kakao",
        }


async def _get_google_user(code: str, redirect_uri: str) -> dict:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            logger.error("google token error: %s", token_resp.text)
            raise HTTPException(status_code=401, detail="구글 인증에 실패했습니다")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="구글 토큰 응답이 올바르지 않습니다")

        user_resp = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="구글 사용자 정보를 가져올 수 없습니다")

        data = user_resp.json()
        return {
            "email": data.get("email"),
            "provider": "google",
        }


async def _find_or_create_user(
    db: AsyncSession,
    email: str | None,
    provider: str,
    guest_user_id: str | None,
) -> tuple[User, bool]:
    """기존 사용자 조회 또는 신규 생성. 게스트 전환도 처리."""
    is_new = False

    if email:
        result = await db.execute(
            select(User).where(User.email == email, User.provider == provider)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, False

    # 게스트 → 로그인 전환: 기존 게스트 유저에 email/provider 연결
    if guest_user_id:
        try:
            guest_uuid = UUID(guest_user_id)
            result = await db.execute(select(User).where(User.id == guest_uuid))
            guest_user = result.scalar_one_or_none()
            if guest_user and guest_user.provider is None:
                guest_user.email = email
                guest_user.provider = provider
                await db.commit()
                await db.refresh(guest_user)
                return guest_user, False
        except ValueError:
            logger.warning("invalid guest_user_id: %s", guest_user_id)

    # 완전 신규 유저
    new_user = User(id=uuid.uuid4(), email=email, provider=provider)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    is_new = True
    return new_user, is_new


@router.get("/kakao")
async def kakao_login_redirect(state: str = Query(...)) -> RedirectResponse:
    redirect_uri = f"{settings.frontend_url}/auth/kakao/callback"
    params = urlencode({
        "client_id": settings.kakao_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    })
    return RedirectResponse(url=f"{KAKAO_AUTH_URL}?{params}")


@router.get("/google")
async def google_login_redirect(state: str = Query(...)) -> RedirectResponse:
    redirect_uri = f"{settings.frontend_url}/auth/google/callback"
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "email profile",
        "state": state,
    })
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{params}")


@router.post("/kakao", response_model=AuthTokenResponse)
async def kakao_callback(
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    oauth_user = await _get_kakao_user(body.code, redirect_uri=f"{settings.frontend_url}/auth/kakao/callback")
    user, is_new = await _find_or_create_user(
        db, oauth_user["email"], oauth_user["provider"], body.guest_user_id
    )
    token = create_access_token(user.id)
    return AuthTokenResponse(
        access_token=token, user_id=str(user.id), is_new_user=is_new
    )


@router.post("/google", response_model=AuthTokenResponse)
async def google_callback(
    body: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    oauth_user = await _get_google_user(body.code, redirect_uri=f"{settings.frontend_url}/auth/google/callback")
    user, is_new = await _find_or_create_user(
        db, oauth_user["email"], oauth_user["provider"], body.guest_user_id
    )
    token = create_access_token(user.id)
    return AuthTokenResponse(
        access_token=token, user_id=str(user.id), is_new_user=is_new
    )


@router.post("/guest", response_model=AuthTokenResponse)
async def guest_login(
    guest_user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AuthTokenResponse:
    """게스트 JWT 발급 — provider=NULL 사용자 생성/재사용 후 토큰 반환."""
    user: User | None = None
    is_new = False

    if guest_user_id:
        try:
            guest_uuid = UUID(guest_user_id)
            result = await db.execute(select(User).where(User.id == guest_uuid))
            user = result.scalar_one_or_none()
        except ValueError:
            logger.warning("invalid guest_user_id: %s", guest_user_id)

    if user is None:
        user = User(id=uuid.uuid4(), provider=None, email=None)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new = True

    token = create_access_token(user.id)
    return AuthTokenResponse(
        access_token=token, user_id=str(user.id), is_new_user=is_new
    )
