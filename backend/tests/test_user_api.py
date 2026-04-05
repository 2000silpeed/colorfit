"""DELETE /api/user/{user_id} — 계정 삭제 API 테스트."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

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


USER_ID_DASHED = "aaaaaaaa-1111-4000-8000-000000000001"
USER_ID_HEX = "aaaaaaaa111140008000000000000001"


@pytest_asyncio.fixture
async def seeded_user(db_session):
    await db_session.execute(text("""
        INSERT INTO users (id, gender, tone_id)
        VALUES (:uid, 'female', 'spring_warm_light')
    """), {"uid": USER_ID_HEX})
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url)
        VALUES (:iid, :uid, 'https://example.com/a.jpg')
    """), {"iid": uuid.uuid4().hex, "uid": USER_ID_HEX})
    await db_session.commit()
    return db_session


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_success(self, client, seeded_user):
        resp = await client.delete(f"/api/user/{USER_ID_DASHED}")
        assert resp.status_code == 204

        result = await seeded_user.execute(
            text("SELECT COUNT(*) FROM users WHERE id = :uid"),
            {"uid": USER_ID_HEX},
        )
        assert result.scalar() == 0

    @pytest.mark.asyncio
    async def test_delete_user_cascades_closet(self, client, seeded_user):
        await client.delete(f"/api/user/{USER_ID_DASHED}")
        result = await seeded_user.execute(
            text("SELECT COUNT(*) FROM closet_items WHERE user_id = :uid"),
            {"uid": USER_ID_HEX},
        )
        assert result.scalar() == 0

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client):
        unknown = str(uuid.uuid4())
        resp = await client.delete(f"/api/user/{unknown}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_invalid_uuid(self, client):
        resp = await client.delete("/api/user/not-a-uuid")
        assert resp.status_code == 422
