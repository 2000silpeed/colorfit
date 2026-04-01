"""Feed API + Outfit API 엔드포인트 테스트.

httpx AsyncClient + 인메모리 SQLite로 테스트.
conftest.py에서 PostgreSQL 전용 타입 → SQLite 호환 처리.
"""

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
    """테스트용 코디 + 상품 데이터를 raw SQL로 삽입."""
    await db_session.execute(text("""
        INSERT INTO products (id, name, brand, category, color_hex, tone_id, price, image_url, gender, silhouette)
        VALUES
        ('prod_001', '아이보리 니트', '무신사 스탠다드', '니트', '#F5F0E1', 'spring_warm_light', 39000, 'https://img.example.com/p1.jpg', 'female', 'fitted'),
        ('prod_002', '베이지 슬랙스', 'COS', '슬랙스', '#C8B89A', 'spring_warm_light', 69000, 'https://img.example.com/p2.jpg', 'female', 'slim'),
        ('prod_003', '로퍼', '유니클로', '로퍼', '#8B7355', 'autumn_warm_mute', 49000, 'https://img.example.com/p3.jpg', 'unisex', NULL)
    """))

    await db_session.execute(text("""
        INSERT INTO outfits (id, item_ids, gender, designed_tpo, designed_season, total_price, is_complete_outfit, tags, scores, reasons)
        VALUES
        ('outfit_001', :items1, 'female', 'commute', 'spring', 157000, 1, :tags1, :scores1, :reasons1),
        ('outfit_002', :items2, 'male', 'casual', 'spring', 39000, 0, :tags2, :scores2, NULL)
    """), {
        "items1": json.dumps(["prod_001", "prod_002", "prod_003"]),
        "tags1": json.dumps(["commute", "office"]),
        "scores1": json.dumps({"pcf": 85.0, "of": 90.0, "ch": 78.0, "pe": 70.0, "sf": 82.0}),
        "reasons1": json.dumps(["퍼스널컬러와 잘 어울려요", "출근 룩에 적합해요"]),
        "items2": json.dumps(["prod_001"]),
        "tags2": json.dumps(["casual"]),
        "scores2": json.dumps({"pcf": 60.0, "of": 50.0, "ch": 45.0, "pe": 80.0, "sf": 55.0}),
    })

    await db_session.commit()


# ---------------------------------------------------------------------------
# GET /api/feed
# ---------------------------------------------------------------------------


class TestFeedEndpoint:
    @pytest.mark.asyncio
    async def test_feed_requires_tone_id(self, client):
        resp = await client.get("/api/feed")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_returns_outfits(self, client, seed_data):
        resp = await client.get("/api/feed", params={"tone_id": "spring_warm_light"})
        assert resp.status_code == 200
        data = resp.json()
        assert "outfits" in data
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert isinstance(data["total"], int)
        assert isinstance(data["has_next"], bool)

    @pytest.mark.asyncio
    async def test_feed_gender_filter(self, client, seed_data):
        resp = await client.get(
            "/api/feed",
            params={"tone_id": "spring_warm_light", "gender": "female"},
        )
        data = resp.json()
        for outfit in data["outfits"]:
            assert outfit["gender"] in ("female", "unisex", None)

    @pytest.mark.asyncio
    async def test_feed_includes_scores_and_reasons(self, client, seed_data):
        resp = await client.get(
            "/api/feed",
            params={"tone_id": "spring_warm_light"},
        )
        data = resp.json()
        if data["outfits"]:
            first = data["outfits"][0]
            assert "scores" in first
            assert "reasons" in first
            assert "soft_score" in first
            assert "final_score" in first

    @pytest.mark.asyncio
    async def test_feed_pagination(self, client, seed_data):
        resp = await client.get(
            "/api/feed",
            params={"tone_id": "spring_warm_light", "page": 1},
        )
        data = resp.json()
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_feed_empty_result(self, client):
        resp = await client.get(
            "/api/feed",
            params={"tone_id": "winter_cool_vivid"},
        )
        data = resp.json()
        assert data["outfits"] == []
        assert data["total"] == 0


# ---------------------------------------------------------------------------
# GET /api/outfit/{id}
# ---------------------------------------------------------------------------


class TestOutfitEndpoint:
    @pytest.mark.asyncio
    async def test_outfit_detail(self, client, seed_data):
        resp = await client.get("/api/outfit/outfit_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "outfit_001"
        assert data["gender"] == "female"
        assert data["designed_tpo"] == "commute"
        assert data["total_price"] == 157000
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_outfit_items_have_fields(self, client, seed_data):
        resp = await client.get("/api/outfit/outfit_001")
        data = resp.json()
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert "brand" in item
        assert "price" in item

    @pytest.mark.asyncio
    async def test_outfit_not_found(self, client, seed_data):
        resp = await client.get("/api/outfit/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_outfit_scores_format(self, client, seed_data):
        resp = await client.get("/api/outfit/outfit_001")
        data = resp.json()
        scores = data["scores"]
        assert "pcf" in scores
        assert "of" in scores
        assert "ch" in scores
        assert "pe" in scores
        assert "sf" in scores
