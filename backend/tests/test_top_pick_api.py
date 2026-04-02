"""Top Pick API 엔드포인트 + 서비스 테스트.

httpx AsyncClient + 인메모리 SQLite로 테스트.
"""

import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import get_db
from app.main import app
from app.services.top_pick import _infer_time_slot, _merge_tpo_list, _generate_highlight_reason


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
    """테스트용 코디 + 상품 데이터."""
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
        ('outfit_002', :items2, 'female', 'casual', 'spring', 39000, 0, :tags2, :scores2, NULL)
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


@pytest_asyncio.fixture
async def seed_with_save(db_session, seed_data):
    """저장 반응이 있는 데이터."""
    await db_session.execute(text("""
        INSERT INTO reactions (user_id, outfit_id, reaction_type, created_at)
        VALUES ('user_001', 'outfit_002', 'save', '2026-04-01T10:00:00')
    """))
    await db_session.commit()


# ---------------------------------------------------------------------------
# 순수 함수 단위 테스트
# ---------------------------------------------------------------------------


class TestInferTimeSlot:
    def test_morning(self):
        assert _infer_time_slot(8) == "morning"

    def test_afternoon(self):
        assert _infer_time_slot(14) == "afternoon"

    def test_evening(self):
        assert _infer_time_slot(20) == "evening"

    def test_late_night(self):
        assert _infer_time_slot(2) == "evening"

    def test_boundary_6(self):
        assert _infer_time_slot(6) == "morning"

    def test_boundary_12(self):
        assert _infer_time_slot(12) == "afternoon"

    def test_boundary_18(self):
        assert _infer_time_slot(18) == "evening"


class TestMergeTpoList:
    def test_merge_morning(self):
        result = _merge_tpo_list(["commute"], current_hour=9)
        assert "commute" in result
        assert "office" in result
        assert "daily" in result

    def test_merge_afternoon(self):
        result = _merge_tpo_list(["date"], current_hour=14)
        assert "date" in result
        assert "casual" in result

    def test_merge_empty_user_tpo(self):
        result = _merge_tpo_list(None, current_hour=20)
        assert "date" in result
        assert "party" in result

    def test_no_duplicates(self):
        result = _merge_tpo_list(["daily"], current_hour=9)
        assert result.count("daily") == 1


class TestGenerateHighlightReason:
    def test_high_pcf(self):
        scores = {"pcf": 90.0, "of": 50.0, "ch": 50.0, "pe": 50.0, "sf": 50.0}
        result = _generate_highlight_reason(scores, "spring_warm_light")
        assert result != ""

    def test_empty_scores(self):
        assert _generate_highlight_reason({}) == ""
        assert _generate_highlight_reason(None) == ""


# ---------------------------------------------------------------------------
# API 엔드포인트 테스트
# ---------------------------------------------------------------------------


class TestTopPickEndpoint:
    @pytest.mark.asyncio
    async def test_requires_tone_id(self, client):
        resp = await client.get("/api/top-pick")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_top_pick(self, client, seed_data):
        resp = await client.get("/api/top-pick", params={"tone_id": "spring_warm_light"})
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "scores" in data
        assert "reasons" in data
        assert "highlight_reason" in data
        assert "source" in data
        assert data["source"] == "db"

    @pytest.mark.asyncio
    async def test_returns_highest_score(self, client, seed_data):
        resp = await client.get(
            "/api/top-pick",
            params={
                "tone_id": "spring_warm_light",
                "gender": "female",
                "tpo": "commute",
                "current_hour": 9,
            },
        )
        data = resp.json()
        assert data["id"] == "outfit_001"  # 고득점 코디

    @pytest.mark.asyncio
    async def test_saved_source(self, client, seed_with_save):
        resp = await client.get(
            "/api/top-pick",
            params={"tone_id": "spring_warm_light", "user_id": "user_001"},
        )
        data = resp.json()
        assert data["source"] == "saved"
        assert data["id"] == "outfit_002"

    @pytest.mark.asyncio
    async def test_time_based_tpo(self, client, seed_data):
        resp_morning = await client.get(
            "/api/top-pick",
            params={"tone_id": "spring_warm_light", "current_hour": 9},
        )
        assert resp_morning.status_code == 200

        resp_evening = await client.get(
            "/api/top-pick",
            params={"tone_id": "spring_warm_light", "current_hour": 20},
        )
        assert resp_evening.status_code == 200

    @pytest.mark.asyncio
    async def test_no_match_returns_404(self, client):
        resp = await client.get(
            "/api/top-pick",
            params={"tone_id": "winter_cool_vivid"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_scores_format(self, client, seed_data):
        resp = await client.get(
            "/api/top-pick",
            params={"tone_id": "spring_warm_light"},
        )
        data = resp.json()
        scores = data["scores"]
        assert "pcf" in scores
        assert "of" in scores
        assert "ch" in scores
        assert "pe" in scores
        assert "sf" in scores

    @pytest.mark.asyncio
    async def test_items_included(self, client, seed_data):
        resp = await client.get(
            "/api/top-pick",
            params={"tone_id": "spring_warm_light"},
        )
        data = resp.json()
        assert isinstance(data["items"], list)
