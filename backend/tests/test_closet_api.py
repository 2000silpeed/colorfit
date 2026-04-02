"""옷장 관리 API 테스트.

GET /api/closet — 옷장 목록 + 퍼스널컬러 적합도 통계 검증.
Task 3.7 구현.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.db.session import get_db
from app.main import app

USER_ID = "aaaaaaaa111140008000000000000001"
OTHER_USER_ID = "bbbbbbbb222240008000000000000002"
USER_ID_DASHED = "aaaaaaaa-1111-4000-8000-000000000001"

ALLNULL_USER_ID = "cccccccc333340008000000000000003"
ALLNULL_USER_ID_DASHED = "cccccccc-3333-4000-8000-000000000003"

ITEM_IDS = [uuid.uuid4().hex for _ in range(7)]


@pytest_asyncio.fixture
async def seeded_db(db_session):
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score, reasons, created_at)
        VALUES
        (:id1, :uid, 'https://example.com/coat.jpg', 'outer', '#F5E6D3', 'spring_warm_light', 85.0, 80.0, NULL, '2026-03-01 10:00:00'),
        (:id2, :uid, 'https://example.com/shirt.jpg', 'top', '#1A1A2E', 'winter_cool_deep', 45.0, 50.0, NULL, '2026-03-02 12:00:00'),
        (:id3, :uid, 'https://example.com/pants.jpg', 'bottom', '#C8B8A8', 'autumn_warm_muted', 72.0, 68.0, NULL, '2026-03-03 14:00:00'),
        (:id4, :uid, 'https://example.com/bag.jpg', 'bag', '#D4A574', 'spring_warm_light', NULL, NULL, NULL, '2026-03-04 16:00:00'),
        (:id5, :other_uid, 'https://example.com/other.jpg', 'top', '#FF0000', 'winter_cool_vivid', 90.0, 88.0, NULL, '2026-03-05 18:00:00'),
        (:id6, :uid, 'https://example.com/shoes.jpg', 'shoes', '#B8860B', 'autumn_warm_deep', 70.0, 65.0, NULL, '2026-03-05 09:00:00'),
        (:id7, :nulluid, 'https://example.com/nullitem.jpg', 'top', '#AAAAAA', NULL, NULL, NULL, NULL, '2026-03-01 10:00:00')
    """), {
        "id1": ITEM_IDS[0], "id2": ITEM_IDS[1], "id3": ITEM_IDS[2],
        "id4": ITEM_IDS[3], "id5": ITEM_IDS[4], "id6": ITEM_IDS[5],
        "id7": ITEM_IDS[6],
        "uid": USER_ID, "other_uid": OTHER_USER_ID,
        "nulluid": ALLNULL_USER_ID,
    })
    await db_session.commit()
    return db_session


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


# ── 옷장 목록 반환 ──


class TestGetClosetItems:
    @pytest.mark.asyncio
    async def test_returns_only_user_items(self, client):
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_excludes_other_user_items(self, client):
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        data = resp.json()
        ids = {item["id"] for item in data["items"]}
        assert ITEM_IDS[4] not in ids

    @pytest.mark.asyncio
    async def test_ordered_by_created_at_desc(self, client):
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        items = resp.json()["items"]
        dates = [i["created_at"] for i in items]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_item_fields_present(self, client):
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        item = resp.json()["items"][0]
        expected_keys = {
            "id", "image_url", "category", "dominant_color_hex",
            "matched_tone_id", "pcf_score", "overall_score",
            "reasons", "created_at",
        }
        assert expected_keys == set(item.keys())

    @pytest.mark.asyncio
    async def test_empty_closet(self, empty_client):
        new_user = str(uuid.uuid4())
        resp = await empty_client.get(f"/api/closet?user_id={new_user}")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ── 통계 계산 ──


class TestGetClosetStats:
    @pytest.mark.asyncio
    async def test_total_count(self, client):
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        stats = resp.json()["stats"]
        assert stats["total_count"] == 5

    @pytest.mark.asyncio
    async def test_average_pcf_excludes_none(self, client):
        """pcf_score가 None인 아이템은 평균 계산에서 제외."""
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        stats = resp.json()["stats"]
        # 85.0 + 45.0 + 72.0 + 70.0 = 272.0 / 4 = 68.0
        assert stats["average_pcf"] == 68.0

    @pytest.mark.asyncio
    async def test_good_count_threshold_70(self, client):
        """pcf_score >= 70 인 아이템만 good_count에 포함 (70.0 경계값 포함)."""
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        stats = resp.json()["stats"]
        # 85.0 >= 70 ✓, 45.0 < 70 ✗, 72.0 >= 70 ✓, 70.0 >= 70 ✓, None 제외
        assert stats["good_count"] == 3

    @pytest.mark.asyncio
    async def test_good_ratio_percentage(self, client):
        """good_ratio = good_count / total_count * 100."""
        resp = await client.get(f"/api/closet?user_id={USER_ID_DASHED}")
        stats = resp.json()["stats"]
        # 3 good / 5 total = 60.0%
        assert stats["good_ratio"] == 60.0

    @pytest.mark.asyncio
    async def test_all_pcf_null_stats(self, client):
        """모든 아이템의 pcf_score가 NULL이면 average_pcf=0, good_count=0."""
        resp = await client.get(f"/api/closet?user_id={ALLNULL_USER_ID_DASHED}")
        stats = resp.json()["stats"]
        assert stats["total_count"] == 1
        assert stats["average_pcf"] == 0.0
        assert stats["good_count"] == 0
        assert stats["good_ratio"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_closet_stats(self, empty_client):
        new_user = str(uuid.uuid4())
        resp = await empty_client.get(f"/api/closet?user_id={new_user}")
        stats = resp.json()["stats"]
        assert stats == {
            "total_count": 0,
            "average_pcf": 0.0,
            "good_count": 0,
            "good_ratio": 0.0,
        }


# ── 에러 케이스 ──


class TestGetClosetValidation:
    @pytest.mark.asyncio
    async def test_missing_user_id_returns_422(self, client):
        resp = await client.get("/api/closet")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, client):
        resp = await client.get("/api/closet?user_id=not-a-uuid")
        assert resp.status_code == 422
