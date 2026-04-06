"""내 아이템 기반 코디 매칭 서비스 테스트.

순수 함수 단위 테스트 + DB 통합 테스트.
"""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.services.closet_outfit_matcher import (
    RGB_DISTANCE_THRESHOLD,
    _apply_hard_filters,
    _exclude_first_match,
    _find_matching_slot,
    _recalculate_scores,
    match_outfits_for_closet_item,
)
from tests.conftest import (  # noqa: F401 — db fixtures
    closet_items_table,
    outfits_table,
    products_table,
)


# ── 헬퍼 ──

def _make_outfit_ns(**overrides) -> SimpleNamespace:
    defaults = {
        "id": "outfit-1",
        "item_ids": ["p1", "p2", "p3"],
        "gender": "female",
        "age_group": "20s",
        "designed_tpo": "commute",
        "designed_season": "spring",
        "total_price": 120000,
        "is_complete_outfit": True,
        "tags": ["commute"],
        "scores": {"pcf": 80, "of": 85, "ch": 70, "pe": 75, "sf": 80},
        "reasons": [],
        "llm_quality_score": 4,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_item(item_id: str, group: str, color_hex: str, **kw) -> dict:
    defaults = {
        "id": item_id,
        "group": group,
        "color_hex": color_hex,
        "tone_id": "spring_warm_light",
        "category": "상의",
        "brand": "TestBrand",
        "price": 40000,
        "image_url": "https://img.test/1.jpg",
        "silhouette": "regular",
        "style_tag": "casual",
    }
    defaults.update(kw)
    return defaults


# ── _find_matching_slot 테스트 ──

class TestFindMatchingSlot:
    def test_exact_color_match(self):
        items = [
            _make_item("p1", "top", "#FF0000"),
            _make_item("p2", "bottom", "#0000FF"),
        ]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result is not None
        assert result["id"] == "p1"

    def test_similar_color_within_threshold(self):
        items = [_make_item("p1", "top", "#FF0000")]
        result = _find_matching_slot("top", "#FF1010", items)
        assert result is not None

    def test_no_match_different_group(self):
        items = [_make_item("p1", "bottom", "#FF0000")]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result is None

    def test_no_match_color_too_far(self):
        items = [_make_item("p1", "top", "#FF0000")]
        result = _find_matching_slot("top", "#0000FF", items)
        assert result is None

    def test_picks_closest_color(self):
        items = [
            _make_item("p1", "top", "#FF3030"),
            _make_item("p2", "top", "#FF0505"),
        ]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result["id"] == "p2"

    def test_no_color_hex_returns_none(self):
        result = _find_matching_slot("top", None, [_make_item("p1", "top", "#FF0000")])
        assert result is None

    def test_item_without_color_hex_skipped(self):
        items = [_make_item("p1", "top", None)]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result is None


# ── _apply_hard_filters 테스트 ──

class TestApplyHardFilters:
    def test_pass_matching_gender(self):
        outfit = _make_outfit_ns(gender="female")
        assert _apply_hard_filters(outfit, "female", None) is True

    def test_pass_unisex_gender(self):
        outfit = _make_outfit_ns(gender="unisex")
        assert _apply_hard_filters(outfit, "female", None) is True

    def test_fail_wrong_gender(self):
        outfit = _make_outfit_ns(gender="male")
        assert _apply_hard_filters(outfit, "female", None) is False

    def test_pass_no_gender_filter(self):
        outfit = _make_outfit_ns(gender="male")
        assert _apply_hard_filters(outfit, None, None) is True

    def test_pass_matching_age_group(self):
        outfit = _make_outfit_ns(age_group="20s")
        assert _apply_hard_filters(outfit, None, "20s") is True

    def test_fail_wrong_age_group(self):
        outfit = _make_outfit_ns(age_group="40plus")
        assert _apply_hard_filters(outfit, None, "20s") is False

    def test_pass_null_outfit_age(self):
        outfit = _make_outfit_ns(age_group=None)
        assert _apply_hard_filters(outfit, None, "20s") is True

    @patch("app.services.closet_outfit_matcher.datetime")
    def test_fail_opposite_season(self, mock_dt):
        mock_dt.now.return_value.month = 7  # summer
        outfit = _make_outfit_ns(designed_season="winter")
        assert _apply_hard_filters(outfit, None, None) is False

    @patch("app.services.closet_outfit_matcher.datetime")
    def test_pass_travel_tpo_ignores_season(self, mock_dt):
        mock_dt.now.return_value.month = 7
        outfit = _make_outfit_ns(designed_season="winter", designed_tpo="travel")
        assert _apply_hard_filters(outfit, None, None) is True


# ── _recalculate_scores 테스트 ──

class TestRecalculateScores:
    def test_returns_all_five_axes(self):
        outfit = _make_outfit_ns()
        items = [
            _make_item("p1", "top", "#B0A6C6", tone_id="summer_cool_soft"),
            _make_item("p2", "bottom", "#8B7D6B", tone_id="autumn_warm_mute"),
            _make_item("p3", "shoes", "#5C4033", tone_id="autumn_warm_deep"),
        ]
        my_item = {
            "id": "ci-1",
            "dominant_color_hex": "#B0A0C0",
            "matched_tone_id": "summer_cool_soft",
        }
        scores = _recalculate_scores(outfit, items, items[0], my_item, "summer_cool_soft", 200000)
        assert set(scores.keys()) == {"pcf", "of", "ch", "pe", "sf"}
        for v in scores.values():
            assert 0.0 <= v <= 100.0

    def test_of_preserved_from_existing(self):
        outfit = _make_outfit_ns(scores={"pcf": 80, "of": 92, "ch": 70, "pe": 75, "sf": 80})
        items = [_make_item("p1", "top", "#FF0000")]
        my_item = {"id": "ci-1", "dominant_color_hex": "#FF0000", "matched_tone_id": "spring_warm_light"}
        scores = _recalculate_scores(outfit, items, items[0], my_item, "spring_warm_light", None)
        assert scores["of"] == 92

    def test_sf_preserved_from_existing(self):
        outfit = _make_outfit_ns(scores={"pcf": 80, "of": 85, "ch": 70, "pe": 75, "sf": 88})
        items = [_make_item("p1", "top", "#FF0000")]
        my_item = {"id": "ci-1", "dominant_color_hex": "#FF0000", "matched_tone_id": "spring_warm_light"}
        scores = _recalculate_scores(outfit, items, items[0], my_item, "spring_warm_light", None)
        assert scores["sf"] == 88

    def test_pe_uses_purchase_cost_only(self):
        outfit = _make_outfit_ns()
        items = [
            _make_item("p1", "top", "#FF0000", price=50000),
            _make_item("p2", "bottom", "#0000FF", price=30000),
        ]
        my_item = {"id": "ci-1", "dominant_color_hex": "#FF0000", "matched_tone_id": "spring_warm_light"}
        scores = _recalculate_scores(outfit, items, items[0], my_item, "spring_warm_light", 100000)
        # PE는 추가 구매 비용(p2: 30000)으로 계산 — budget_max=100000 대비 저렴
        assert scores["pe"] > 0

    def test_ch_includes_my_item_color(self):
        outfit = _make_outfit_ns()
        items = [
            _make_item("p1", "top", "#FF0000"),
            _make_item("p2", "bottom", "#00FF00"),
            _make_item("p3", "shoes", "#0000FF"),
        ]
        my_item = {"id": "ci-1", "dominant_color_hex": "#FF5500", "matched_tone_id": "spring_warm_light"}
        scores = _recalculate_scores(outfit, items, items[0], my_item, "spring_warm_light", None)
        # CH가 계산되었는지 확인 (p2, p3 + 내 아이템 = 3색)
        assert 0 <= scores["ch"] <= 100


# ── match_outfits_for_closet_item 통합 테스트 ──

USER_ID = uuid.uuid4().hex
CLOSET_ITEM_ID = uuid.uuid4().hex


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """테스트용 코디 + 상품 + 옷장아이템 데이터를 삽입한다."""
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score)
        VALUES (:cid, :uid, 'https://img.test/my-top.jpg', 'top', '#E8B4B8', 'spring_warm_light', 85.0, 80.0)
    """), {"cid": CLOSET_ITEM_ID, "uid": USER_ID})

    await db_session.execute(text("""
        INSERT INTO products (id, name, brand, category, color_hex, tone_id, price, image_url, gender)
        VALUES
        ('prod-top-1', '핑크 블라우스', 'BrandA', '블라우스', '#E8B0B5', 'spring_warm_light', 35000, 'https://img.test/top1.jpg', 'female'),
        ('prod-bottom-1', '베이지 슬랙스', 'BrandB', '슬랙스', '#D2B48C', 'autumn_warm_mute', 45000, 'https://img.test/bottom1.jpg', 'female'),
        ('prod-shoes-1', '베이지 로퍼', 'BrandC', '로퍼', '#C8A882', 'autumn_warm_mute', 55000, 'https://img.test/shoes1.jpg', 'female')
    """))

    await db_session.execute(text("""
        INSERT INTO outfits (id, item_ids, gender, age_group, designed_tpo, designed_season, total_price, is_complete_outfit, tags, scores, reasons, llm_quality_score)
        VALUES ('outfit-match-1', :items, 'female', '20s', 'commute', 'spring', 135000, 1, :tags, :scores, :reasons, 4)
    """), {
        "items": json.dumps(["prod-top-1", "prod-bottom-1", "prod-shoes-1"]),
        "tags": json.dumps(["commute"]),
        "scores": json.dumps({"pcf": 82, "of": 88, "ch": 75, "pe": 70, "sf": 80}),
        "reasons": json.dumps(["추천 이유"]),
    })

    await db_session.commit()

    # 피드 캐시를 직접 세팅 (SQLite에서 ARRAY/JSONB 호환 문제 회피)
    import time as _time
    from app.services.feed_service import _feed_cache

    _feed_cache["outfits"] = [
        SimpleNamespace(
            id="outfit-match-1",
            item_ids=["prod-top-1", "prod-bottom-1", "prod-shoes-1"],
            gender="female",
            age_group="20s",
            designed_tpo="commute",
            designed_season="spring",
            total_price=135000,
            is_complete_outfit=True,
            tags=["commute"],
            scores={"pcf": 82, "of": 88, "ch": 75, "pe": 70, "sf": 80},
            reasons=["추천 이유"],
            llm_quality_score=4,
        ),
    ]
    _feed_cache["item_map"] = {
        "outfit-match-1": [
            {"id": "prod-top-1", "brand": "BrandA", "tone_id": "spring_warm_light",
             "category": "블라우스", "silhouette": None, "group": "top",
             "color_hex": "#E8B0B5", "price": 35000, "image_url": "https://img.test/top1.jpg",
             "style_tag": None},
            {"id": "prod-bottom-1", "brand": "BrandB", "tone_id": "autumn_warm_mute",
             "category": "슬랙스", "silhouette": None, "group": "bottom",
             "color_hex": "#D2B48C", "price": 45000, "image_url": "https://img.test/bottom1.jpg",
             "style_tag": None},
            {"id": "prod-shoes-1", "brand": "BrandC", "tone_id": "autumn_warm_mute",
             "category": "로퍼", "silhouette": None, "group": "shoes",
             "color_hex": "#C8A882", "price": 55000, "image_url": "https://img.test/shoes1.jpg",
             "style_tag": None},
        ],
    }
    _feed_cache["expires_at"] = _time.time() + 600

    yield db_session

    _feed_cache["outfits"] = None
    _feed_cache["item_map"] = None
    _feed_cache["expires_at"] = 0.0


class TestMatchOutfitsIntegration:
    @pytest.mark.asyncio
    async def test_returns_matching_outfit(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        assert result["strategy_used"] == "db_match"
        assert result["total_count"] >= 1
        outfit = result["outfits"][0]
        assert outfit["source"] == "db_match"
        assert outfit["db_outfit_id"] == "outfit-match-1"

    @pytest.mark.asyncio
    async def test_outfit_contains_my_item(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
        )
        outfit = result["outfits"][0]
        closet_items = [it for it in outfit["items"] if it["source"] == "closet"]
        assert len(closet_items) == 1
        assert closet_items[0]["label"] == "내 옷"

    @pytest.mark.asyncio
    async def test_purchase_summary_excludes_my_item(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
        )
        outfit = result["outfits"][0]
        summary = outfit["purchase_summary"]
        assert summary["my_items_count"] == 1
        assert summary["purchase_items_count"] == 2  # bottom + shoes
        assert summary["purchase_total"] == 100000  # 45000 + 55000

    @pytest.mark.asyncio
    async def test_scores_recalculated(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
        )
        outfit = result["outfits"][0]
        scores = outfit["scores"]
        assert "pcf" in scores
        assert "ch" in scores
        assert 0 <= scores["pcf"] <= 100
        assert 0 <= scores["ch"] <= 100

    @pytest.mark.asyncio
    async def test_nonexistent_closet_item_returns_empty(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=str(uuid.uuid4()),
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
        )
        assert result["outfits"] == []
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_gender_filter_excludes_mismatch(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
            gender="male",
        )
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_has_reasons(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
        )
        if result["total_count"] > 0:
            outfit = result["outfits"][0]
            assert len(outfit["reasons"]) >= 1

    @pytest.mark.asyncio
    async def test_limit_respected(self, seeded_db):
        result = await match_outfits_for_closet_item(
            seeded_db,
            closet_item_id=CLOSET_ITEM_ID,
            user_id=USER_ID,
            user_tone_id="spring_warm_light",
            limit=1,
        )
        assert len(result["outfits"]) <= 1


# ── Codex 리뷰 반영 추가 테스트 ──


class TestExcludeFirstMatch:
    def test_removes_only_first_duplicate(self):
        items = [
            {"id": "a", "v": 1},
            {"id": "b", "v": 2},
            {"id": "a", "v": 3},
        ]
        result = _exclude_first_match(items, "a")
        assert len(result) == 2
        assert result[0]["id"] == "b"
        assert result[1]["id"] == "a"
        assert result[1]["v"] == 3

    def test_no_match_returns_all(self):
        items = [{"id": "x"}, {"id": "y"}]
        assert len(_exclude_first_match(items, "z")) == 2


class TestPeZeroPurchaseCost:
    def test_zero_purchase_cost_gives_max_score(self):
        outfit = _make_outfit_ns()
        items = [_make_item("p1", "top", "#FF0000", price=0)]
        my_item = {"id": "ci-1", "dominant_color_hex": "#FF0000", "matched_tone_id": "spring_warm_light"}
        scores = _recalculate_scores(outfit, items, items[0], my_item, "spring_warm_light", 100000)
        assert scores["pe"] == 100.0


class TestRgbDistanceBoundary:
    def test_exactly_at_threshold_no_match(self):
        """RGB 거리 정확히 60.0 → 매칭 안 됨 (< 60 엄격 비교)."""
        # RGB (255,0,0) vs (195,0,0) = sqrt(60^2) = 60.0
        items = [_make_item("p1", "top", "#C30000")]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result is None

    def test_just_under_threshold_matches(self):
        """RGB 거리 59.x → 매칭됨."""
        items = [_make_item("p1", "top", "#C40000")]
        result = _find_matching_slot("top", "#FF0000", items)
        assert result is not None
