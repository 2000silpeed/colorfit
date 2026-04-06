"""POST /api/closet/outfits API 통합 테스트.

정상 응답 / 빈 옷장 / 존재하지 않는 아이템 / 유효성 검증 에러 처리.
Task 6.4 구현.
"""

import json
import time
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import get_db
from app.main import app
from app.services.feed_service import _feed_cache

# hex(대시 없음) 형식 통일: ORM UUID 타입(SQLite→hex 변환) + raw SQL 문자열 비교 모두 호환
USER_ID = uuid.uuid4().hex
CLOSET_ITEM_ID = uuid.uuid4().hex
CLOSET_ITEM_ID_2 = uuid.uuid4().hex

NO_TONE_USER_ID = uuid.uuid4().hex

NONEXISTENT_USER_ID = str(uuid.uuid4())


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """사용자 + 옷장 아이템 + 카탈로그 상품 시드."""
    # 사용자 (톤 진단 완료)
    await db_session.execute(text("""
        INSERT INTO users (id, email, provider, gender, tone_id, budget_max, age_group)
        VALUES (:uid, 'test@test.com', 'google', 'female', 'spring_warm_light', 200000, '20s')
    """), {"uid": USER_ID})

    # 톤 미진단 사용자
    await db_session.execute(text("""
        INSERT INTO users (id, email, provider, gender, tone_id, budget_max, age_group)
        VALUES (:uid, 'notone@test.com', 'google', 'female', NULL, 200000, '20s')
    """), {"uid": NO_TONE_USER_ID})

    # 옷장 아이템 1: 코럴 핑크 블라우스
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score)
        VALUES (:cid, :uid, 'https://img.test/coral.jpg', '블라우스', '#E8967C', 'spring_warm_light', 88.0, 85.0)
    """), {"cid": CLOSET_ITEM_ID, "uid": USER_ID})

    # 옷장 아이템 2: 베이지 슬랙스
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score)
        VALUES (:cid, :uid, 'https://img.test/slacks.jpg', '슬랙스', '#D2B48C', 'autumn_warm_mute', 75.0, 72.0)
    """), {"cid": CLOSET_ITEM_ID_2, "uid": USER_ID})

    # 카탈로그 상품
    await db_session.execute(text("""
        INSERT INTO products (id, name, brand, category, color_hex, tone_id, price, image_url, gender, age_group)
        VALUES
        ('p-bottom-1', '와이드 팬츠 베이지', 'BrandA', '면바지', '#D2B48C', 'autumn_warm_mute', 49000, 'https://img.test/pants.jpg', 'female', '20s'),
        ('p-shoes-1', '메리제인 베이지', 'BrandB', '플랫슈즈', '#C8A882', 'autumn_warm_mute', 89000, 'https://img.test/shoes.jpg', 'female', '20s'),
        ('p-top-1', '린넨 셔츠 크림', 'BrandC', '셔츠', '#FFFDD0', 'spring_warm_light', 55000, 'https://img.test/shirt.jpg', 'female', '20s'),
        ('p-shoes-2', '스니커즈 크림', 'BrandD', '스니커즈', '#FFFDD0', 'spring_warm_light', 69000, 'https://img.test/sneakers.jpg', 'female', '20s')
    """))

    await db_session.commit()

    # 피드 캐시 비우기 (전략 A 매칭 안 되게 → B fallback 테스트)
    _feed_cache["outfits"] = []
    _feed_cache["item_map"] = {}
    _feed_cache["expires_at"] = time.time() + 600

    yield db_session

    _feed_cache["outfits"] = None
    _feed_cache["item_map"] = None
    _feed_cache["expires_at"] = 0.0


@pytest_asyncio.fixture
async def client(seeded_db):
    async def override_get_db():
        yield seeded_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def empty_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── 정상 응답 ──


class TestClosetOutfitsSuccess:
    @pytest.mark.asyncio
    async def test_single_item_returns_outfits(self, client):
        """단일 아이템 요청 → 코디 결과 반환."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "outfits" in data
        assert "total_count" in data
        assert "strategy_used" in data
        assert isinstance(data["outfits"], list)

    @pytest.mark.asyncio
    async def test_single_item_outfit_structure(self, client):
        """코디 결과에 필수 필드가 모두 존재."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        data = resp.json()
        if data["total_count"] > 0:
            outfit = data["outfits"][0]
            assert "id" in outfit
            assert outfit["source"] in ("db_match", "dynamic_combo")
            assert "total_score" in outfit
            assert set(outfit["scores"].keys()) == {"pcf", "of", "ch", "pe", "sf"}
            assert "reasons" in outfit
            assert "items" in outfit
            assert "purchase_summary" in outfit

    @pytest.mark.asyncio
    async def test_single_item_has_closet_source(self, client):
        """코디 내 아이템 중 source='closet'이 존재."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        data = resp.json()
        if data["total_count"] > 0:
            outfit = data["outfits"][0]
            sources = [it["source"] for it in outfit["items"]]
            assert "closet" in sources

    @pytest.mark.asyncio
    async def test_multi_item_returns_dynamic_combo(self, client):
        """복수 아이템 → 전략 B(dynamic_combo) 직행."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_ids": [CLOSET_ITEM_ID, CLOSET_ITEM_ID_2],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy_used"] == "dynamic_combo"

    @pytest.mark.asyncio
    async def test_multi_item_both_closet_items_present(self, client):
        """복수 아이템 결과에 두 옷장 아이템 모두 포함."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_ids": [CLOSET_ITEM_ID, CLOSET_ITEM_ID_2],
        })
        data = resp.json()
        if data["total_count"] > 0:
            outfit = data["outfits"][0]
            closet_ids = {it["id"] for it in outfit["items"] if it["source"] == "closet"}
            assert CLOSET_ITEM_ID in closet_ids
            assert CLOSET_ITEM_ID_2 in closet_ids

    @pytest.mark.asyncio
    async def test_purchase_summary_correct(self, client):
        """purchase_summary에 내 아이템 수 + 추가 구매 비용 올바름."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        data = resp.json()
        if data["total_count"] > 0:
            summary = data["outfits"][0]["purchase_summary"]
            assert summary["my_items_count"] >= 1
            assert summary["purchase_items_count"] >= 0
            assert summary["purchase_total"] >= 0

    @pytest.mark.asyncio
    async def test_limit_parameter_respected(self, client):
        """limit 파라미터 적용 확인."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "limit": 2,
        })
        data = resp.json()
        assert len(data["outfits"]) <= 2

    @pytest.mark.asyncio
    async def test_tpo_filter_applied(self, client):
        """TPO 필터 파라미터 전달 (에러 없이 응답)."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "tpo": "commute",
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_budget_max_applied(self, client):
        """budget_max 필터 전달 (에러 없이 응답)."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "budget_max": 80000,
        })
        assert resp.status_code == 200
        data = resp.json()
        for outfit in data["outfits"]:
            assert outfit["purchase_summary"]["purchase_total"] <= 80000


# ── 빈 옷장 / 존재하지 않는 아이템 ──


class TestClosetOutfitsEmpty:
    @pytest.mark.asyncio
    async def test_nonexistent_closet_item(self, client):
        """존재하지 않는 옷장 아이템 ID → 빈 결과."""
        fake_id = uuid.uuid4().hex
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": fake_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 0
        assert data["outfits"] == []

    @pytest.mark.asyncio
    async def test_nonexistent_multi_items(self, client):
        """존재하지 않는 복수 아이템 → 빈 결과."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_ids": [uuid.uuid4().hex, uuid.uuid4().hex],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 0


# ── 에러 처리 ──


class TestClosetOutfitsErrors:
    @pytest.mark.asyncio
    async def test_no_item_id_returns_422(self, client):
        """closet_item_id도 closet_item_ids도 없으면 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_both_item_ids_returns_422(self, client):
        """closet_item_id와 closet_item_ids 동시 지정 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "closet_item_ids": [CLOSET_ITEM_ID_2],
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_user_id_returns_422(self, client):
        """유효하지 않은 user_id 형식 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": "not-a-uuid",
            "closet_item_id": CLOSET_ITEM_ID,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404(self, client):
        """존재하지 않는 사용자 → 404."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": NONEXISTENT_USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_no_tone_user_returns_422(self, client):
        """톤 미진단 사용자 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": NO_TONE_USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
        })
        assert resp.status_code == 422
        assert "tone_id" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_limit_too_high_returns_422(self, client):
        """limit > 20 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "limit": 50,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_zero_returns_422(self, client):
        """limit < 1 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "user_id": USER_ID,
            "closet_item_id": CLOSET_ITEM_ID,
            "limit": 0,
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_user_id_returns_422(self, client):
        """user_id 누락 → 422."""
        resp = await client.post("/api/closet/outfits", json={
            "closet_item_id": CLOSET_ITEM_ID,
        })
        assert resp.status_code == 422
