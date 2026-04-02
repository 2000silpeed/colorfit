"""A vs B 비교 API + 서비스 테스트."""

import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import get_db
from app.main import app
from app.services.comparator import compare_outfits


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
        INSERT INTO outfits (id, item_ids, gender, designed_tpo, designed_season, total_price, is_complete_outfit, tags, scores)
        VALUES
        ('outfit_a', :items_a, 'female', 'commute', 'spring', 108000, 1, :tags_a, :scores_a),
        ('outfit_b', :items_b, 'female', 'casual', 'spring', 39000, 0, :tags_b, :scores_b)
    """), {
        "items_a": json.dumps(["prod_001", "prod_002"]),
        "tags_a": json.dumps(["commute", "office"]),
        "scores_a": json.dumps({"pcf": 85.0, "of": 90.0, "ch": 78.0, "pe": 70.0, "sf": 82.0}),
        "items_b": json.dumps(["prod_001"]),
        "tags_b": json.dumps(["casual"]),
        "scores_b": json.dumps({"pcf": 60.0, "of": 50.0, "ch": 45.0, "pe": 80.0, "sf": 55.0}),
    })

    await db_session.commit()


# ---------------------------------------------------------------------------
# 순수 함수 단위 테스트
# ---------------------------------------------------------------------------


class TestCompareOutfits:
    def test_a_wins(self):
        scores_a = {"pcf": 90.0, "of": 80.0, "ch": 70.0, "pe": 60.0, "sf": 85.0}
        scores_b = {"pcf": 60.0, "of": 50.0, "ch": 45.0, "pe": 80.0, "sf": 55.0}
        result = compare_outfits(scores_a, scores_b)
        assert result["winner"] == "A"
        assert len(result["axis_comparison"]) == 5
        assert result["total_a"] > result["total_b"]

    def test_b_wins(self):
        scores_a = {"pcf": 40.0, "of": 30.0, "ch": 35.0, "pe": 50.0, "sf": 45.0}
        scores_b = {"pcf": 90.0, "of": 85.0, "ch": 80.0, "pe": 70.0, "sf": 88.0}
        result = compare_outfits(scores_a, scores_b)
        assert result["winner"] == "B"

    def test_tie(self):
        scores = {"pcf": 70.0, "of": 70.0, "ch": 70.0, "pe": 70.0, "sf": 70.0}
        result = compare_outfits(scores, scores)
        assert result["winner"] == "tie"
        assert result["decisive_factor"]["diff"] == 0.0

    def test_decisive_factor_is_largest_diff(self):
        scores_a = {"pcf": 90.0, "of": 50.0, "ch": 70.0, "pe": 60.0, "sf": 70.0}
        scores_b = {"pcf": 50.0, "of": 50.0, "ch": 70.0, "pe": 60.0, "sf": 70.0}
        result = compare_outfits(scores_a, scores_b)
        assert result["decisive_factor"]["axis"] == "pcf"
        assert result["decisive_factor"]["diff"] == 40.0

    def test_axis_comparison_has_all_axes(self):
        scores_a = {"pcf": 80.0, "of": 70.0, "ch": 60.0, "pe": 50.0, "sf": 75.0}
        scores_b = {"pcf": 75.0, "of": 65.0, "ch": 55.0, "pe": 55.0, "sf": 70.0}
        result = compare_outfits(scores_a, scores_b)
        axes = [ac["axis"] for ac in result["axis_comparison"]]
        assert axes == ["pcf", "of", "ch", "pe", "sf"]

    def test_pe_b_wins_axis(self):
        scores_a = {"pcf": 80.0, "of": 70.0, "ch": 60.0, "pe": 40.0, "sf": 75.0}
        scores_b = {"pcf": 75.0, "of": 65.0, "ch": 55.0, "pe": 90.0, "sf": 70.0}
        result = compare_outfits(scores_a, scores_b)
        pe_comp = next(ac for ac in result["axis_comparison"] if ac["axis"] == "pe")
        assert pe_comp["winner"] == "B"
        assert pe_comp["diff"] == -50.0

    def test_explanation_contains_axis_name(self):
        scores_a = {"pcf": 90.0, "of": 50.0, "ch": 50.0, "pe": 50.0, "sf": 50.0}
        scores_b = {"pcf": 50.0, "of": 50.0, "ch": 50.0, "pe": 50.0, "sf": 50.0}
        result = compare_outfits(scores_a, scores_b, tone_id="spring_warm_light")
        explanation = result["decisive_factor"]["explanation"]
        assert "퍼스널컬러 적합도" in explanation
        assert "A" in explanation

    def test_decisive_factor_winner_matches_overall(self):
        """decisive_factor.winner가 overall winner와 일치해야 한다."""
        scores_a = {"pcf": 90.0, "of": 80.0, "ch": 70.0, "pe": 20.0, "sf": 75.0}
        scores_b = {"pcf": 50.0, "of": 50.0, "ch": 50.0, "pe": 90.0, "sf": 50.0}
        result = compare_outfits(scores_a, scores_b)
        assert result["winner"] == "A"
        assert result["decisive_factor"]["winner"] == "A"

    def test_explanation_uses_winner_actual_score(self):
        """winner 측의 실제 점수(60)가 mid 템플릿을 생성해야 한다."""
        scores_a = {"pcf": 60.0, "of": 60.0, "ch": 60.0, "pe": 60.0, "sf": 60.0}
        scores_b = {"pcf": 50.0, "of": 50.0, "ch": 50.0, "pe": 50.0, "sf": 50.0}
        result = compare_outfits(scores_a, scores_b)
        explanation = result["decisive_factor"]["explanation"]
        assert "비교적" in explanation or "무난" in explanation or "안정감" in explanation or "만족" in explanation or "전체적" in explanation

    def test_empty_scores(self):
        result = compare_outfits({}, {})
        assert result["winner"] == "tie"
        assert result["total_a"] == 0.0
        assert result["total_b"] == 0.0


# ---------------------------------------------------------------------------
# API 엔드포인트 테스트
# ---------------------------------------------------------------------------


class TestCompareEndpoint:
    @pytest.mark.asyncio
    async def test_requires_ids(self, client):
        resp = await client.get("/api/compare")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_two_ids(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_three_ids_rejected(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "a,b,c"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_compare_returns_result(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a,outfit_b"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["outfit_a"]["id"] == "outfit_a"
        assert data["outfit_b"]["id"] == "outfit_b"
        assert data["winner"] == "A"
        assert len(data["axis_comparison"]) == 5
        assert "decisive_factor" in data

    @pytest.mark.asyncio
    async def test_compare_with_tone_id(self, client, seed_data):
        resp = await client.get(
            "/api/compare",
            params={"ids": "outfit_a,outfit_b", "tone_id": "spring_warm_light"},
        )
        data = resp.json()
        assert data["decisive_factor"]["explanation"] != ""

    @pytest.mark.asyncio
    async def test_outfit_not_found(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a,nonexistent"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_scores_included(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a,outfit_b"})
        data = resp.json()
        assert data["outfit_a"]["scores"]["pcf"] == 85.0
        assert data["outfit_b"]["scores"]["pcf"] == 60.0

    @pytest.mark.asyncio
    async def test_image_url_included(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a,outfit_b"})
        data = resp.json()
        assert data["outfit_a"]["image_url"] is not None

    @pytest.mark.asyncio
    async def test_same_outfit_is_tie(self, client, seed_data):
        resp = await client.get("/api/compare", params={"ids": "outfit_a,outfit_a"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["winner"] == "tie"
