"""POST /api/onboarding 엔드포인트 테스트.

httpx AsyncClient + 인메모리 SQLite로 테스트.
"""

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


VALID_BODY = {
    "gender": "female",
    "tone_id": "spring_warm_light",
    "tpo_list": ["commute", "date"],
    "style_moods": ["casual", "minimal"],
    "budget_min": 30000,
    "budget_max": 100000,
    "style_seeds": {
        "mood_seed": "casual",
        "silhouette_seed": "slim",
        "color_seed": "neutral",
        "price_seed": "mid",
    },
    "seed_confidence": 4,
}


class TestOnboardingEndpoint:
    @pytest.mark.asyncio
    async def test_create_user_returns_user_id(self, client):
        resp = await client.post("/api/onboarding", json=VALID_BODY)
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert len(data["user_id"]) > 0

    @pytest.mark.asyncio
    async def test_user_saved_to_db(self, client, db_session):
        resp = await client.post("/api/onboarding", json=VALID_BODY)
        user_id = resp.json()["user_id"]

        row = await db_session.execute(
            text("SELECT gender, tone_id, budget_min, budget_max FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        user = row.fetchone()
        assert user is not None
        assert user[0] == "female"
        assert user[1] == "spring_warm_light"
        assert user[2] == 30000
        assert user[3] == 100000

    @pytest.mark.asyncio
    async def test_style_seed_saved_to_db(self, client, db_session):
        resp = await client.post("/api/onboarding", json=VALID_BODY)
        user_id = resp.json()["user_id"]

        row = await db_session.execute(
            text("SELECT mood_seed, silhouette_seed, color_seed, price_seed, seed_confidence FROM style_seeds WHERE user_id = :uid"),
            {"uid": user_id},
        )
        seed = row.fetchone()
        assert seed is not None
        assert seed[0] == "casual"
        assert seed[1] == "slim"
        assert seed[2] == "neutral"
        assert seed[3] == "mid"
        assert seed[4] == 4

    @pytest.mark.asyncio
    async def test_without_style_seeds(self, client, db_session):
        body = {
            "gender": "male",
            "tone_id": "winter_cool_deep",
            "tpo_list": [],
            "style_moods": [],
        }
        resp = await client.post("/api/onboarding", json=body)
        assert resp.status_code == 200
        user_id = resp.json()["user_id"]

        row = await db_session.execute(
            text("SELECT COUNT(*) FROM style_seeds WHERE user_id = :uid"),
            {"uid": user_id},
        )
        assert row.scalar() == 0

    @pytest.mark.asyncio
    async def test_invalid_gender_rejected(self, client):
        body = {**VALID_BODY, "gender": "other"}
        resp = await client.post("/api/onboarding", json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_tone_id_rejected(self, client):
        body = {**VALID_BODY}
        del body["tone_id"]
        resp = await client.post("/api/onboarding", json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_tone_id_rejected(self, client):
        body = {**VALID_BODY, "tone_id": ""}
        resp = await client.post("/api/onboarding", json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_tpo_primary_secondary_set(self, client, db_session):
        resp = await client.post("/api/onboarding", json=VALID_BODY)
        user_id = resp.json()["user_id"]

        row = await db_session.execute(
            text("SELECT tpo_primary, tpo_secondary FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        user = row.fetchone()
        assert user[0] == "commute"
        assert user[1] == "date"
