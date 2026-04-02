"""저장 목록 API 테스트 — GET /api/saved"""

import json

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


@pytest_asyncio.fixture
async def seed_data(db_session):
    await db_session.execute(text("""
        INSERT INTO products (id, name, brand, category, color_hex, tone_id, price, image_url, gender, silhouette)
        VALUES
        ('prod_001', '아이보리 니트', '무신사 스탠다드', '니트', '#F5F0E1', 'spring_warm_light', 39000, 'https://img.example.com/p1.jpg', 'female', 'fitted'),
        ('prod_002', '베이지 슬랙스', 'COS', '슬랙스', '#C8B89A', 'spring_warm_light', 69000, 'https://img.example.com/p2.jpg', 'female', 'slim')
    """))

    await db_session.execute(text("""
        INSERT INTO outfits (id, item_ids, gender, designed_tpo, designed_season, total_price, is_complete_outfit, tags, scores, reasons)
        VALUES
        ('outfit_001', :items1, 'female', 'commute', 'spring', 108000, 1, :tags1, :scores1, :reasons1),
        ('outfit_002', :items2, 'female', 'casual', 'spring', 39000, 0, :tags2, :scores2, NULL)
    """), {
        "items1": json.dumps(["prod_001", "prod_002"]),
        "tags1": json.dumps(["commute"]),
        "scores1": json.dumps({"pcf": 85.0, "of": 90.0, "ch": 78.0, "pe": 70.0, "sf": 82.0}),
        "reasons1": json.dumps(["퍼스널컬러와 잘 어울려요"]),
        "items2": json.dumps(["prod_001"]),
        "tags2": json.dumps(["casual"]),
        "scores2": json.dumps({"pcf": 60.0, "of": 50.0, "ch": 45.0, "pe": 80.0, "sf": 55.0}),
    })

    # 저장 반응 삽입
    await db_session.execute(text("""
        INSERT INTO reactions (user_id, outfit_id, reaction_type, created_at)
        VALUES
        ('user_001', 'outfit_001', 'save', '2026-04-01T10:00:00'),
        ('user_001', 'outfit_002', 'save', '2026-04-01T11:00:00'),
        ('user_001', 'outfit_001', 'dislike', '2026-04-01T09:00:00')
    """))
    await db_session.commit()


class TestSavedEndpoint:
    @pytest.mark.asyncio
    async def test_requires_user_id(self, client):
        resp = await client.get("/api/saved")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_saved_outfits(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["outfits"]) == 2

    @pytest.mark.asyncio
    async def test_recent_sort_order(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001", "sort_by": "recent"})
        data = resp.json()
        # outfit_002가 나중에 저장되었으므로 먼저
        assert data["outfits"][0]["id"] == "outfit_002"
        assert data["outfits"][1]["id"] == "outfit_001"

    @pytest.mark.asyncio
    async def test_score_sort_order(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001", "sort_by": "score"})
        data = resp.json()
        assert data["outfits"][0]["id"] == "outfit_001"  # 고점수

    @pytest.mark.asyncio
    async def test_price_sort_order(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001", "sort_by": "price"})
        data = resp.json()
        assert data["outfits"][0]["id"] == "outfit_002"  # 39000 < 108000

    @pytest.mark.asyncio
    async def test_empty_saved(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "no_saves_user"})
        data = resp.json()
        assert data["total"] == 0
        assert data["outfits"] == []

    @pytest.mark.asyncio
    async def test_includes_scores(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001"})
        data = resp.json()
        outfit = next(o for o in data["outfits"] if o["id"] == "outfit_001")
        assert outfit["scores"]["pcf"] == 85.0

    @pytest.mark.asyncio
    async def test_includes_image_url(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001"})
        data = resp.json()
        outfit = next(o for o in data["outfits"] if o["id"] == "outfit_001")
        assert outfit["image_url"] is not None

    @pytest.mark.asyncio
    async def test_excludes_dislikes(self, client, seed_data):
        resp = await client.get("/api/saved", params={"user_id": "user_001"})
        data = resp.json()
        # dislike는 포함되지 않아야 함
        ids = [o["id"] for o in data["outfits"]]
        assert len(ids) == 2  # save만 2개
