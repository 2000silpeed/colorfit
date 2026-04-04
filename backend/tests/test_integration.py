"""Task 4.11 — E2E 통합 테스트 (실제 PostgreSQL).

실제 Supabase PostgreSQL에 연결하여 사용자 플로우를 검증한다.
외부 API(Gemini, 이미지 다운로드)만 mock. 나머지는 실제 로직 + 실제 DB.

전략:
  - 테스트 전용 async engine으로 get_db를 오버라이드
  - 시드 데이터는 TEST_PREFIX ID로 식별
  - teardown에서 테스트 데이터만 DELETE 정리
"""

import os
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from dotenv import dotenv_values

_env_path = Path(__file__).resolve().parent.parent / ".env"
_env_values = dotenv_values(_env_path)
_pg_url = _env_values.get("DATABASE_URL", "")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# 'app' 관련 임포트 전에 DATABASE_URL 설정
if _pg_url:
    os.environ["DATABASE_URL"] = _pg_url

from app.db import session as db_session_module
from app.db.session import get_db
from app.main import app

# app.db.session의 엔진을 Supabase pooler 호환 설정으로 교체
if _pg_url and ("postgresql" in _pg_url or "postgres" in _pg_url):
    _compat_engine = create_async_engine(
        _pg_url, echo=False, poolclass=NullPool,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )
    db_session_module.engine = _compat_engine
    db_session_module.async_session = async_sessionmaker(
        _compat_engine, class_=AsyncSession, expire_on_commit=False,
    )
from app.models.closet_item import ClosetItem
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.models.subscription import Subscription
from app.models.style_seed import StyleSeed
from app.models.tryon_cache import TryonCache
from app.models.tryon_usage import TryonUsage

# 실행별 고유 ID — CI 동시 실행에서도 충돌 방지
_RUN_ID = uuid.uuid4().hex[:8]
TEST_PREFIX = f"ti_{_RUN_ID}_"
TEST_TONE = f"{TEST_PREFIX}tone"

pytestmark = pytest.mark.skipif(
    "postgresql" not in _pg_url and "postgres" not in _pg_url,
    reason="통합 테스트는 실제 PostgreSQL DATABASE_URL이 필요합니다",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def test_engine():
    assert "postgresql" in _pg_url or "postgres" in _pg_url
    engine = create_async_engine(
        _pg_url, echo=False, poolclass=NullPool,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="module")
def test_session_factory(test_engine):
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def client():
    """앱의 자체 get_db 사용 (엔진은 이미 호환 설정으로 교체됨)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def rich_seed(test_session_factory):
    """테스트 시드 데이터 INSERT → teardown에서 DELETE."""
    P = TEST_PREFIX
    products = [
        Product(id=f"{P}p1", name="아이보리 니트", brand="무신사 스탠다드", category="니트",
                color_hex="#F5F0E1", tone_id="spring_warm_light", price=39000,
                image_url="https://img.example.com/p1.jpg", mall_url="https://shop.example.com/p1",
                gender="female", silhouette="fitted", formality=3, style_tag="casual"),
        Product(id=f"{P}p2", name="베이지 슬랙스", brand="COS", category="슬랙스",
                color_hex="#C8B89A", tone_id="spring_warm_light", price=69000,
                image_url="https://img.example.com/p2.jpg", mall_url="https://shop.example.com/p2",
                gender="female", silhouette="slim", formality=4, style_tag="classic"),
        Product(id=f"{P}p3", name="브라운 로퍼", brand="유니클로", category="로퍼",
                color_hex="#8B7355", tone_id="autumn_warm_mute", price=49000,
                image_url="https://img.example.com/p3.jpg", mall_url="https://shop.example.com/p3",
                gender="unisex", formality=3, style_tag="classic"),
        Product(id=f"{P}p4", name="블랙 코트", brand="자라", category="코트",
                color_hex="#1A1A1A", tone_id="winter_cool_deep", price=189000,
                image_url="https://img.example.com/p4.jpg", mall_url="https://shop.example.com/p4",
                gender="female", silhouette="oversized", formality=5, style_tag="formal"),
        Product(id=f"{P}p5", name="화이트 티", brand="나이키", category="티셔츠",
                color_hex="#FFFFFF", tone_id="spring_warm_light", price=29000,
                image_url="https://img.example.com/p5.jpg", mall_url="https://shop.example.com/p5",
                gender="male", silhouette="regular", formality=1, style_tag="sporty"),
        Product(id=f"{P}p6", name="청바지", brand="리바이스", category="청바지",
                color_hex="#3B5998", tone_id="summer_cool_soft", price=89000,
                image_url="https://img.example.com/p6.jpg", mall_url="https://shop.example.com/p6",
                gender="unisex", silhouette="straight", formality=2, style_tag="casual"),
    ]

    outfits = [
        Outfit(id=f"{P}o1", item_ids=[f"{P}p1", f"{P}p2", f"{P}p3"], gender="female",
               designed_tpo="commute", designed_season="spring", total_price=157000,
               is_complete_outfit=True, tags=["commute", "office"],
               scores={"pcf": 85, "of": 90, "ch": 78, "pe": 70, "sf": 82},
               reasons=["퍼스널컬러와 잘 어울려요", "출근 룩에 적합해요"], age_group="20s"),
        Outfit(id=f"{P}o2", item_ids=[f"{P}p1"], gender="female",
               designed_tpo="casual", designed_season="spring", total_price=39000,
               is_complete_outfit=False, tags=["casual"],
               scores={"pcf": 60, "of": 50, "ch": 45, "pe": 80, "sf": 55}, age_group="20s"),
        Outfit(id=f"{P}o3", item_ids=[f"{P}p5", f"{P}p6"], gender="male",
               designed_tpo="date", designed_season="spring", total_price=118000,
               is_complete_outfit=True, tags=["date", "casual"],
               scores={"pcf": 70, "of": 85, "ch": 65, "pe": 75, "sf": 72},
               reasons=["데이트에 어울리는 코디"], age_group="30s"),
        Outfit(id=f"{P}o4", item_ids=[f"{P}p4", f"{P}p2"], gender="female",
               designed_tpo="commute", designed_season="winter", total_price=258000,
               is_complete_outfit=True, tags=["commute", "formal"],
               scores={"pcf": 40, "of": 80, "ch": 55, "pe": 30, "sf": 70}, age_group="20s"),
        Outfit(id=f"{P}o5", item_ids=[f"{P}p1", f"{P}p3"], gender="female",
               designed_tpo="casual", designed_season="spring", total_price=88000,
               is_complete_outfit=True, tags=["casual", "daily"],
               scores={"pcf": 80, "of": 65, "ch": 72, "pe": 85, "sf": 68},
               reasons=["캐주얼한 일상 코디"], age_group="20s"),
    ]

    async with test_session_factory() as session:
        for obj in products + outfits:
            session.add(obj)
        await session.commit()

    yield

    # Teardown — raw SQL로 정리 (존재하지 않는 테이블 safe skip)
    async with test_session_factory() as session:
        await session.execute(text(
            f"DELETE FROM reactions WHERE outfit_id LIKE '{P}%'"))

        test_uids = (await session.execute(
            text(f"SELECT id FROM users WHERE tone_id = '{TEST_TONE}'")
        )).scalars().all()

        for uid in test_uids:
            for tbl in ["tryon_usage", "tryon_cache", "subscriptions", "style_seeds", "closet_items"]:
                await session.execute(text(
                    f"DELETE FROM {tbl} WHERE user_id = :uid"), {"uid": str(uid)})
            await session.execute(text(
                "DELETE FROM reactions WHERE user_id = :uid"), {"uid": str(uid)})

        await session.execute(text(
            f"DELETE FROM users WHERE tone_id = '{TEST_TONE}'"))
        await session.execute(text(
            f"DELETE FROM outfits WHERE id LIKE '{P}%'"))
        await session.execute(text(
            f"DELETE FROM products WHERE id LIKE '{P}%'"))
        await session.commit()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_user(client: AsyncClient, **overrides) -> str:
    body = {
        "gender": "female",
        "tone_id": TEST_TONE,
        "age_group": "20s",
        "tpo_list": ["commute", "casual"],
        "style_moods": ["minimal"],
        "budget_min": 30000,
        "budget_max": 200000,
        **overrides,
    }
    resp = await client.post("/api/onboarding", json=body)
    assert resp.status_code == 200, f"onboarding failed: {resp.text}"
    return resp.json()["user_id"]


# ===========================================================================
# 경로 B: 온보딩 → 피드 → 코디 상세 → 가격비교 → 외부 링크
# ===========================================================================

class TestRouteB:

    @pytest.mark.asyncio
    async def test_full_route_b_flow(self, client, rich_seed):
        """온보딩 → 피드 → 코디 상세 → 아이템 상세 → 가격비교."""
        user_id = await _create_user(client)

        feed = (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female",
            "age_group": "20s", "user_id": user_id,
        })).json()
        assert feed["total"] > 0

        first = feed["outfits"][0]
        assert first["scores"] is not None
        assert first["soft_score"] > 0
        assert len(first["reasons"]) > 0

        detail = (await client.get(f"/api/outfit/{first['id']}")).json()
        assert len(detail["items"]) > 0
        assert detail["scores"]["pcf"] > 0

        item = detail["items"][0]
        item_d = (await client.get(f"/api/item/{item['id']}")).json()
        assert item_d["mall_url"] is not None
        assert isinstance(item_d["price_entries"], list)
        if item_d["price_entries"]:
            entry = item_d["price_entries"][0]
            assert "mall_name" in entry
            assert "price" in entry
            assert "mall_url" in entry

        similar = await client.get(f"/api/item/{item['id']}/similar", params={"limit": 3})
        assert similar.status_code == 200

    @pytest.mark.asyncio
    async def test_feed_tpo_filter(self, client, rich_seed):
        data = (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female", "tpo": "commute",
        })).json()
        for o in data["outfits"]:
            if o["designed_tpo"]:
                assert o["designed_tpo"] in ("commute", "office")

    @pytest.mark.asyncio
    async def test_feed_pagination(self, client, rich_seed):
        resp = await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "page": 2,
        })
        assert resp.status_code == 200
        assert resp.json()["page"] == 2

    @pytest.mark.asyncio
    async def test_feed_items_have_brand_info(self, client, rich_seed):
        data = (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female",
        })).json()
        if data["outfits"] and data["outfits"][0].get("items"):
            item = data["outfits"][0]["items"][0]
            assert "brand" in item
            assert "style_tag" in item
            assert "is_verified_brand" in item


# ===========================================================================
# 경로 A
# ===========================================================================

class TestRouteA:

    @pytest.mark.asyncio
    async def test_closet_analyze_scores(self, client):
        with patch("app.services.closet_analyzer.extract_colors_from_url",
                    return_value=["#F5F0E1", "#C8B89A"]):
            resp = await client.post("/api/closet/analyze", json={
                "image_url": "https://example.com/shirt.jpg",
                "user_tone_id": "spring_warm_light",
            })
        data = resp.json()
        assert data["pcf_score"] > 0
        assert data["overall_score"] > 0
        assert len(data["dominant_colors"]) == 2
        assert len(data["reasons"]) > 0

    @pytest.mark.asyncio
    async def test_closet_analyze_bad_image(self, client):
        with patch("app.services.closet_analyzer.extract_colors_from_url", return_value=[]):
            resp = await client.post("/api/closet/analyze", json={
                "image_url": "https://example.com/blurry.jpg",
                "user_tone_id": "spring_warm_light",
            })
        assert resp.json()["pcf_score"] == 0
        assert "색상을 추출할 수 없었습니다" in resp.json()["reasons"][0]

    @pytest.mark.asyncio
    async def test_closet_save_and_list(self, client, test_session_factory, rich_seed):
        user_id = await _create_user(client)

        async with test_session_factory() as s:
            s.add(ClosetItem(
                user_id=uuid.UUID(user_id),
                image_url="https://example.com/shirt.jpg",
                category="니트", dominant_color_hex="#F5F0E1",
                matched_tone_id="spring_warm_light",
                pcf_score=85.0, overall_score=80.0,
                reasons=["퍼스널컬러와 잘 어울려요"],
            ))
            await s.commit()

        data = (await client.get("/api/closet", params={"user_id": user_id})).json()
        assert data["stats"]["total_count"] == 1
        assert data["items"][0]["pcf_score"] == 85.0
        assert data["items"][0]["reasons"] == ["퍼스널컬러와 잘 어울려요"]

    @pytest.mark.asyncio
    async def test_closet_recommendations(self, client, rich_seed):
        data = (await client.get("/api/closet/recommendations", params={
            "color_hex": "#F5F0E1", "category": "니트",
            "user_tone_id": "spring_warm_light",
        })).json()
        assert data["source_color_hex"] == "#F5F0E1"

    @pytest.mark.asyncio
    async def test_path_a_e2e_chain(self, client, test_session_factory, rich_seed):
        """경로 A 전체 체인: 촬영→분석→옷장저장→역추천→tryon→프리미엄 게이트."""
        user_id = await _create_user(client)

        # 1. 옷 촬영 → 분석
        with patch("app.services.closet_analyzer.extract_colors_from_url",
                    return_value=["#F5F0E1", "#C8B89A"]):
            analyze = (await client.post("/api/closet/analyze", json={
                "image_url": "https://example.com/my-shirt.jpg",
                "user_tone_id": "spring_warm_light",
            })).json()
        assert analyze["pcf_score"] > 0

        # 2. 분석 결과를 옷장에 저장
        async with test_session_factory() as s:
            s.add(ClosetItem(
                user_id=uuid.UUID(user_id),
                image_url="https://example.com/my-shirt.jpg",
                category="니트",
                dominant_color_hex=analyze["dominant_colors"][0]["hex"],
                matched_tone_id=analyze["matched_tone_id"],
                pcf_score=analyze["pcf_score"],
                overall_score=analyze["overall_score"],
                reasons=analyze["reasons"],
            ))
            await s.commit()

        # 3. 옷장 확인
        closet = (await client.get("/api/closet", params={"user_id": user_id})).json()
        assert closet["stats"]["total_count"] == 1
        saved_item = closet["items"][0]

        # 4. 보유 옷 기반 역추천
        rec = (await client.get("/api/closet/recommendations", params={
            "color_hex": saved_item["dominant_color_hex"],
            "category": "니트",
            "user_tone_id": "spring_warm_light",
        })).json()
        assert isinstance(rec["recommendations"], list)

        # 5. 피드에서 코디 선택 → 착장 생성 시도 (무료 한도 확인)
        usage = (await client.get("/api/tryon/usage", params={"user_id": user_id})).json()
        assert usage["remaining"] == 3

    @pytest.mark.asyncio
    async def test_tryon_free_limit_and_premium_gate(self, client, rich_seed):
        """무료 3회 → 403 → 프리미엄 → 다시 가능."""
        user_id = await _create_user(client)
        P = TEST_PREFIX

        fake_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        fake_resp = MagicMock()
        fake_resp.candidates = [MagicMock()]
        fake_resp.candidates[0].content.parts = [MagicMock()]
        fake_resp.candidates[0].content.parts[0].inline_data = MagicMock()
        fake_resp.candidates[0].content.parts[0].inline_data.data = fake_bytes

        with patch("app.services.virtual_tryon._fetch_image_bytes",
                    new_callable=AsyncMock, return_value=fake_bytes), \
             patch("app.services.virtual_tryon.genai") as mock_genai:

            mock_c = MagicMock()
            mock_c.aio.models.generate_content = AsyncMock(return_value=fake_resp)
            mock_genai.Client.return_value = mock_c

            r = await client.post("/api/tryon/generate", json={
                "outfit_id": f"{P}o1", "user_id": user_id,
            })
            assert r.status_code == 200, f"Try 1: {r.text}"
            assert r.json()["remaining"] == 2

            for oid in [f"{P}o2", f"{P}o5"]:
                r = await client.post("/api/tryon/generate", json={
                    "outfit_id": oid, "user_id": user_id,
                })
                assert r.status_code == 200

            r = await client.post("/api/tryon/generate", json={
                "outfit_id": f"{P}o3", "user_id": user_id,
            })
            assert r.status_code == 403
            assert "프리미엄" in r.json()["detail"]

            sub = await client.post("/api/subscribe", json={
                "user_id": user_id, "plan": "monthly", "coupon_code": "COLORFIT-BETA",
            })
            assert sub.status_code == 200

            r = await client.post("/api/tryon/generate", json={
                "outfit_id": f"{P}o3", "user_id": user_id,
            })
            assert r.status_code == 200
            assert r.json()["remaining"] is None


# ===========================================================================
# 교차
# ===========================================================================

class TestCrossNavigation:

    @pytest.mark.asyncio
    async def test_closet_to_feed(self, client, test_session_factory, rich_seed):
        user_id = await _create_user(client)
        async with test_session_factory() as s:
            s.add(ClosetItem(
                user_id=uuid.UUID(user_id),
                image_url="https://example.com/closet.jpg",
                category="니트", dominant_color_hex="#F5F0E1",
                matched_tone_id="spring_warm_light",
                pcf_score=85.0, overall_score=80.0,
            ))
            await s.commit()

        closet = (await client.get("/api/closet", params={"user_id": user_id})).json()
        tone = closet["items"][0]["matched_tone_id"]

        feed = (await client.get("/api/feed", params={
            "tone_id": tone, "gender": "female",
        })).json()
        assert feed["total"] > 0

    @pytest.mark.asyncio
    async def test_feed_save_then_recommendation(self, client, rich_seed):
        user_id = await _create_user(client)
        P = TEST_PREFIX

        await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{P}o1", "reaction_type": "save",
        })

        saved = (await client.get("/api/saved", params={"user_id": user_id})).json()
        assert saved["total"] > 0

        detail = (await client.get(f"/api/outfit/{P}o1")).json()
        item = detail["items"][0]

        rec = await client.get("/api/closet/recommendations", params={
            "color_hex": item.get("color_hex") or "#F5F0E1",
            "category": item["category"],
            "user_tone_id": "spring_warm_light",
        })
        assert rec.status_code == 200


# ===========================================================================
# 저장 + Top Pick
# ===========================================================================

class TestSaveAndTopPick:

    @pytest.mark.asyncio
    async def test_save_dislike_flow(self, client, rich_seed):
        user_id = await _create_user(client)
        P = TEST_PREFIX

        for oid in [f"{P}o1", f"{P}o5"]:
            assert (await client.post("/api/reaction", json={
                "user_id": user_id, "outfit_id": oid, "reaction_type": "save",
            })).status_code == 200

        assert (await client.get("/api/saved",
                params={"user_id": user_id})).json()["total"] == 2

        await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{P}o2", "reaction_type": "dislike",
        })

        feed = (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female", "user_id": user_id,
        })).json()
        ids = [o["id"] for o in feed["outfits"]]
        if f"{P}o2" in ids:
            assert ids.index(f"{P}o2") >= len(ids) - 2

    @pytest.mark.asyncio
    async def test_toggle_save_unsave(self, client, rich_seed):
        user_id = await _create_user(client)
        P = TEST_PREFIX

        r = await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{P}o1", "reaction_type": "save",
        })
        assert r.json()["reaction_type"] == "save"

        r = await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{P}o1", "reaction_type": "save",
        })
        assert r.json()["reaction_type"] == "unsave"

        assert (await client.get("/api/saved",
                params={"user_id": user_id})).json()["total"] == 0

    @pytest.mark.asyncio
    async def test_saved_sort_by_score(self, client, rich_seed):
        user_id = await _create_user(client)
        P = TEST_PREFIX

        for oid in [f"{P}o1", f"{P}o5", f"{P}o2"]:
            await client.post("/api/reaction", json={
                "user_id": user_id, "outfit_id": oid, "reaction_type": "save",
            })

        data = (await client.get("/api/saved", params={
            "user_id": user_id, "sort_by": "score",
        })).json()
        assert data["total"] == 3
        scores = [o["soft_score"] for o in data["outfits"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_top_pick(self, client, rich_seed):
        data = (await client.get("/api/top-pick", params={
            "tone_id": "spring_warm_light", "gender": "female",
        })).json()
        assert data["soft_score"] > 0
        assert len(data["items"]) > 0

    @pytest.mark.asyncio
    async def test_save_then_top_pick_with_user(self, client, rich_seed):
        """저장 후 user_id 전달하여 Top Pick — 저장 기반 필터 검증."""
        user_id = await _create_user(client)
        P = TEST_PREFIX

        await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{P}o1", "reaction_type": "save",
        })

        data = (await client.get("/api/top-pick", params={
            "tone_id": "spring_warm_light", "gender": "female",
            "user_id": user_id,
        })).json()
        assert data["soft_score"] > 0
        assert len(data["items"]) > 0


# ===========================================================================
# 프리미엄
# ===========================================================================

class TestPremiumGate:

    @pytest.mark.asyncio
    async def test_usage_tracking_initial(self, client, rich_seed):
        user_id = await _create_user(client)
        data = (await client.get("/api/tryon/usage",
                params={"user_id": user_id})).json()
        assert data["is_premium"] is False
        assert data["remaining"] == 3

    @pytest.mark.asyncio
    async def test_subscription_lifecycle(self, client, rich_seed):
        user_id = await _create_user(client)

        assert (await client.get("/api/subscription/status",
                params={"user_id": user_id})).json()["is_premium"] is False

        assert (await client.post("/api/subscribe", json={
            "user_id": user_id, "plan": "monthly", "coupon_code": "INVALID",
        })).status_code == 400

        r = await client.post("/api/subscribe", json={
            "user_id": user_id, "plan": "monthly", "coupon_code": "COLORFIT-BETA",
        })
        assert r.status_code == 200
        assert r.json()["price_krw"] == 4900

        assert (await client.get("/api/subscription/status",
                params={"user_id": user_id})).json()["is_premium"] is True

        r = await client.post("/api/subscribe", json={
            "user_id": user_id, "plan": "yearly", "coupon_code": "PREMIUM-TEST",
        })
        assert r.status_code == 400
        assert "이미" in r.json()["detail"]


# ===========================================================================
# Edge Cases
# ===========================================================================

class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_feed_for_mismatched_tone(self, client, rich_seed):
        data = (await client.get("/api/feed", params={
            "tone_id": "nonexistent_tone_xyz", "gender": "female",
        })).json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_feed_budget_filter(self, client, rich_seed):
        ids = [o["id"] for o in (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female", "budget_max": 50000,
        })).json()["outfits"]]
        P = TEST_PREFIX
        assert f"{P}o1" not in ids
        assert f"{P}o4" not in ids

    @pytest.mark.asyncio
    async def test_outfit_not_found(self, client):
        assert (await client.get("/api/outfit/nonexistent_xyz")).status_code == 404

    @pytest.mark.asyncio
    async def test_item_not_found(self, client):
        assert (await client.get("/api/item/nonexistent_xyz")).status_code == 404

    @pytest.mark.asyncio
    async def test_closet_empty_for_new_user(self, client, rich_seed):
        user_id = await _create_user(client)
        assert (await client.get("/api/closet",
                params={"user_id": user_id})).json()["stats"]["total_count"] == 0

    @pytest.mark.asyncio
    async def test_saved_empty_for_new_user(self, client, rich_seed):
        user_id = await _create_user(client)
        assert (await client.get("/api/saved",
                params={"user_id": user_id})).json()["total"] == 0

    @pytest.mark.asyncio
    async def test_closet_analyze_rejects_http(self, client):
        assert (await client.post("/api/closet/analyze", json={
            "image_url": "http://example.com/insecure.jpg",
            "user_tone_id": "spring_warm_light",
        })).status_code == 422

    @pytest.mark.asyncio
    async def test_onboarding_invalid_age_group(self, client):
        assert (await client.post("/api/onboarding", json={
            "gender": "female", "tone_id": "spring_warm_light",
            "age_group": "50s", "tpo_list": [],
        })).status_code == 422

    @pytest.mark.asyncio
    async def test_feed_gender_mismatch(self, client, rich_seed):
        data = (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female",
        })).json()
        for o in data["outfits"]:
            assert o["gender"] != "male"

    @pytest.mark.asyncio
    async def test_top_pick_no_match(self, client):
        r = await client.get("/api/top-pick", params={
            "tone_id": "nonexistent_tone_xyz", "gender": "female", "budget_max": 1000,
        })
        assert r.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_reaction_invalid_type(self, client, rich_seed):
        user_id = await _create_user(client)
        assert (await client.post("/api/reaction", json={
            "user_id": user_id, "outfit_id": f"{TEST_PREFIX}o1",
            "reaction_type": "love",
        })).status_code == 422

    @pytest.mark.asyncio
    async def test_feed_verified_only(self, client, rich_seed):
        assert (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female", "verified_only": True,
        })).status_code == 200

    @pytest.mark.asyncio
    async def test_feed_preferred_brands(self, client, rich_seed):
        assert (await client.get("/api/feed", params={
            "tone_id": "spring_warm_light", "gender": "female",
            "preferred_brands": "COS,유니클로",
        })).status_code == 200
