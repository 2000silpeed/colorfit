"""POST /api/auth/kakao, /api/auth/google 엔드포인트 테스트.

OAuth 외부 호출은 mock, DB 저장/조회는 인메모리 SQLite로 테스트.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from unittest.mock import AsyncMock, patch

from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def _mock_kakao_user(email="test@kakao.com"):
    return {"email": email, "provider": "kakao"}


def _mock_google_user(email="test@gmail.com"):
    return {"email": email, "provider": "google"}


async def _insert_guest_user(db_session, guest_id: str, gender: str = "female", tone_id: str = "spring_warm_light"):
    """raw SQL로 게스트 유저 삽입 (provider=NULL)"""
    await db_session.execute(
        text("INSERT INTO users (id, gender, tone_id) VALUES (:id, :g, :t)"),
        {"id": guest_id, "g": gender, "t": tone_id},
    )
    await db_session.commit()


async def _get_user_by_id(db_session, user_id: str):
    """raw SQL로 유저 조회"""
    row = await db_session.execute(
        text("SELECT id, email, provider, gender, tone_id FROM users WHERE id = :uid"),
        {"uid": user_id},
    )
    return row.fetchone()


async def _count_users(db_session) -> int:
    row = await db_session.execute(text("SELECT COUNT(*) FROM users"))
    return row.scalar()


class TestKakaoLogin:
    @pytest.mark.asyncio
    @patch("app.routers.auth._get_kakao_user", new_callable=AsyncMock, return_value=_mock_kakao_user())
    async def test_new_user_created(self, mock_kakao, client, db_session):
        resp = await client.post("/api/auth/kakao", json={"code": "test-code"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["is_new_user"] is True
        assert data["token_type"] == "bearer"
        assert len(data["user_id"]) > 0

        count = await _count_users(db_session)
        assert count == 1

    @pytest.mark.asyncio
    @patch("app.routers.auth._get_kakao_user", new_callable=AsyncMock, return_value=_mock_kakao_user())
    async def test_existing_user_login(self, mock_kakao, client, db_session):
        resp1 = await client.post("/api/auth/kakao", json={"code": "code1"})
        user_id_1 = resp1.json()["user_id"]

        resp2 = await client.post("/api/auth/kakao", json={"code": "code2"})
        assert resp2.status_code == 200
        assert resp2.json()["user_id"] == user_id_1
        assert resp2.json()["is_new_user"] is False

        count = await _count_users(db_session)
        assert count == 1

    @pytest.mark.asyncio
    @patch("app.routers.auth._get_kakao_user", new_callable=AsyncMock, return_value=_mock_kakao_user())
    async def test_guest_to_login_transition(self, mock_kakao, client, db_session):
        # 게스트 유저 삽입 (ORM UUID는 SQLite에서 hex32로 저장됨)
        guest_uuid = uuid.uuid4()
        guest_hex = guest_uuid.hex  # 대시 없는 32자
        await db_session.execute(
            text("INSERT INTO users (id, gender, tone_id) VALUES (:id, :g, :t)"),
            {"id": guest_hex, "g": "female", "t": "spring_warm_light"},
        )
        await db_session.commit()

        # 프론트엔드는 대시 포함 UUID 문자열을 전송
        resp = await client.post(
            "/api/auth/kakao",
            json={"code": "test-code", "guest_user_id": str(guest_uuid)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_new_user"] is False

        count = await _count_users(db_session)
        assert count == 1


class TestGoogleLogin:
    @pytest.mark.asyncio
    @patch("app.routers.auth._get_google_user", new_callable=AsyncMock, return_value=_mock_google_user())
    async def test_new_user_created(self, mock_google, client, db_session):
        resp = await client.post("/api/auth/google", json={"code": "test-code"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["is_new_user"] is True
        assert len(data["user_id"]) > 0

    @pytest.mark.asyncio
    @patch("app.routers.auth._get_google_user", new_callable=AsyncMock, return_value=_mock_google_user())
    async def test_kakao_google_separate_accounts(self, mock_google, client, db_session):
        """같은 이메일이라도 provider가 다르면 별도 계정"""
        await db_session.execute(
            text("INSERT INTO users (id, email, provider) VALUES (:id, :e, :p)"),
            {"id": str(uuid.uuid4()), "e": "test@gmail.com", "p": "kakao"},
        )
        await db_session.commit()

        resp = await client.post("/api/auth/google", json={"code": "test-code"})
        assert resp.status_code == 200
        assert resp.json()["is_new_user"] is True

        count = await _count_users(db_session)
        assert count == 2


class TestJwtService:
    def test_create_and_verify_token(self):
        from app.services.jwt import create_access_token, verify_access_token
        uid = uuid.uuid4()
        token = create_access_token(uid)
        assert verify_access_token(token) == uid

    def test_invalid_token_returns_none(self):
        from app.services.jwt import verify_access_token
        assert verify_access_token("invalid.token.here") is None

    def test_empty_token_returns_none(self):
        from app.services.jwt import verify_access_token
        assert verify_access_token("") is None
