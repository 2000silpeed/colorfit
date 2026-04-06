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
    DYNAMIC_COMBO_LIMIT,
    FULL_OUTFIT_SLOTS,
    OPTIONAL_SLOTS,
    RGB_DISTANCE_THRESHOLD,
    _apply_hard_filters,
    _build_dynamic_result,
    _compute_dynamic_scores,
    _determine_needed_slots,
    _exclude_first_match,
    _find_matching_slot,
    _generate_dynamic_combos,
    _greedy_select_combo,
    _recalculate_scores,
    _score_candidate_for_slot,
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
        assert "db_match" in result["strategy_used"]
        assert result["total_count"] >= 1
        db_outfits = [o for o in result["outfits"] if o["source"] == "db_match"]
        assert len(db_outfits) >= 1
        assert db_outfits[0]["db_outfit_id"] == "outfit-match-1"

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


# ── 전략 B: 동적 코디 조합 테스트 ──

# 외부 쇼핑몰 스타일 테스트 데이터
# (무신사/W컨셉 스타일 상품명과 가격대를 참고한 가상 데이터)

def _make_product_ns(**overrides):
    """Product ORM 객체를 흉내내는 SimpleNamespace."""
    defaults = {
        "id": f"prod-{uuid.uuid4().hex[:8]}",
        "name": "테스트 상품",
        "brand": "TestBrand",
        "category": "상의",
        "color_hex": "#D4A574",
        "tone_id": "autumn_warm_mute",
        "price": 39000,
        "image_url": "https://image.musinsa.com/test.jpg",
        "mall_url": "https://musinsa.com/test",
        "mall_name": "무신사",
        "tags": ["casual"],
        "gender": "female",
        "silhouette": "regular",
        "formality": 3,
        "age_group": "20s",
        "style_tag": "casual",
        "last_observed_at": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestDetermineNeededSlots:
    def test_single_top_needs_bottom_shoes(self):
        required, optional = _determine_needed_slots(["top"])
        assert "bottom" in required
        assert "shoes" in required
        assert "top" not in required

    def test_single_bottom_needs_top_shoes(self):
        required, optional = _determine_needed_slots(["bottom"])
        assert "top" in required
        assert "shoes" in required

    def test_multi_top_bag_excludes_owned(self):
        required, optional = _determine_needed_slots(["top", "bag"])
        assert "top" not in required
        assert "bag" not in required
        assert "bottom" in required
        assert "shoes" in required

    def test_multi_top_bottom_shoes_all_owned(self):
        required, _ = _determine_needed_slots(["top", "bottom", "shoes"])
        assert required == []

    def test_onepiece_needs_shoes_bag(self):
        required, optional = _determine_needed_slots(["onepiece"])
        assert "shoes" in required
        assert "bag" in required

    def test_empty_input(self):
        required, optional = _determine_needed_slots([])
        assert required == []
        assert optional == []


class TestScoreCandidateForSlot:
    def test_same_tone_gets_highest_tone_score(self):
        product = _make_product_ns(tone_id="spring_warm_light", color_hex="#E8B4B8", price=39000)
        score_same = _score_candidate_for_slot(product, ["#E8B4B8"], "spring_warm_light")

        product2 = _make_product_ns(tone_id="winter_cool_vivid", color_hex="#E8B4B8", price=39000)
        score_diff = _score_candidate_for_slot(product2, ["#E8B4B8"], "spring_warm_light")

        assert score_same > score_diff

    def test_compatible_tone_mid_score(self):
        product = _make_product_ns(tone_id="spring_warm_bright", color_hex="#D4A574", price=39000)
        score = _score_candidate_for_slot(product, ["#E8B4B8"], "spring_warm_light")
        assert 0.5 < score < 1.0

    def test_similar_color_scores_higher(self):
        # 가까운 색상
        p_close = _make_product_ns(color_hex="#E8B0B5", tone_id="spring_warm_light", price=39000)
        score_close = _score_candidate_for_slot(p_close, ["#E8B4B8"], "spring_warm_light")
        # 먼 색상
        p_far = _make_product_ns(color_hex="#0000FF", tone_id="spring_warm_light", price=39000)
        score_far = _score_candidate_for_slot(p_far, ["#E8B4B8"], "spring_warm_light")
        assert score_close > score_far

    def test_no_tone_gets_low_score(self):
        product = _make_product_ns(tone_id=None, color_hex="#D4A574", price=39000)
        score = _score_candidate_for_slot(product, ["#E8B4B8"], "spring_warm_light")
        assert score < 0.5

    def test_cheap_item_price_bonus(self):
        p_cheap = _make_product_ns(tone_id="spring_warm_light", color_hex="#E8B4B8", price=10000)
        p_expensive = _make_product_ns(tone_id="spring_warm_light", color_hex="#E8B4B8", price=200000)
        s_cheap = _score_candidate_for_slot(p_cheap, ["#E8B4B8"], "spring_warm_light")
        s_expensive = _score_candidate_for_slot(p_expensive, ["#E8B4B8"], "spring_warm_light")
        assert s_cheap > s_expensive


class TestComputeDynamicScores:
    def test_returns_all_five_axes(self):
        my_items = [{"dominant_color_hex": "#E8B4B8", "matched_tone_id": "spring_warm_light"}]
        combo = [
            {"color_hex": "#D2B48C", "tone_id": "autumn_warm_mute", "price": 45000},
            {"color_hex": "#8B7D6B", "tone_id": "autumn_warm_deep", "price": 55000},
        ]
        scores = _compute_dynamic_scores(my_items, combo, "spring_warm_light", 200000)
        assert set(scores.keys()) == {"pcf", "of", "ch", "pe", "sf"}
        for v in scores.values():
            assert 0.0 <= v <= 100.0

    def test_zero_purchase_cost_pe_100(self):
        my_items = [{"dominant_color_hex": "#E8B4B8", "matched_tone_id": "spring_warm_light"}]
        combo = [{"color_hex": "#D2B48C", "tone_id": "autumn_warm_mute", "price": 0}]
        scores = _compute_dynamic_scores(my_items, combo, "spring_warm_light", 100000)
        assert scores["pe"] == 100.0

    def test_no_budget_pe_default(self):
        my_items = [{"dominant_color_hex": "#E8B4B8", "matched_tone_id": "spring_warm_light"}]
        combo = [{"color_hex": "#D2B48C", "tone_id": "autumn_warm_mute", "price": 50000}]
        scores = _compute_dynamic_scores(my_items, combo, "spring_warm_light", None)
        assert scores["pe"] == 50.0

    def test_high_budget_pe_high(self):
        my_items = [{"dominant_color_hex": "#E8B4B8", "matched_tone_id": "spring_warm_light"}]
        combo = [{"color_hex": "#D2B48C", "tone_id": "autumn_warm_mute", "price": 10000}]
        scores = _compute_dynamic_scores(my_items, combo, "spring_warm_light", 500000)
        assert scores["pe"] > 60.0


class TestBuildDynamicResult:
    def test_result_structure(self):
        my_items = [{"id": "ci-1", "category": "셔츠", "image_url": "https://img/my.jpg"}]
        combo = [
            {"id": "p1", "category": "슬랙스", "image_url": "https://img/p1.jpg", "brand": "BrandA", "price": 45000},
            {"id": "p2", "category": "로퍼", "image_url": "https://img/p2.jpg", "brand": "BrandB", "price": 55000},
        ]
        scores = {"pcf": 80, "of": 50, "ch": 70, "pe": 65, "sf": 60}
        result = _build_dynamic_result(my_items, combo, scores, 65.0, "spring_warm_light")

        assert result["source"] == "dynamic_combo"
        assert result["db_outfit_id"] is None
        assert result["total_score"] == 65.0
        assert len(result["items"]) == 3
        assert result["items"][0]["source"] == "closet"
        assert result["items"][0]["label"] == "내 옷"
        assert result["items"][1]["source"] == "catalog"
        assert result["purchase_summary"]["my_items_count"] == 1
        assert result["purchase_summary"]["purchase_items_count"] == 2
        assert result["purchase_summary"]["purchase_total"] == 100000

    def test_multi_my_items(self):
        my_items = [
            {"id": "ci-1", "category": "셔츠", "image_url": "https://img/my1.jpg"},
            {"id": "ci-2", "category": "가방", "image_url": "https://img/my2.jpg"},
        ]
        combo = [{"id": "p1", "category": "슬랙스", "image_url": "https://img/p1.jpg", "brand": "B", "price": 45000}]
        scores = {"pcf": 80, "of": 50, "ch": 70, "pe": 65, "sf": 60}
        result = _build_dynamic_result(my_items, combo, scores, 65.0, "spring_warm_light")

        assert result["purchase_summary"]["my_items_count"] == 2
        closet_items = [it for it in result["items"] if it["source"] == "closet"]
        assert len(closet_items) == 2


# ── 전략 B 통합 테스트 (외부 상품 데이터 기반) ──

USER_ID_B = uuid.uuid4().hex
CLOSET_ITEM_ID_B1 = uuid.uuid4().hex
CLOSET_ITEM_ID_B2 = uuid.uuid4().hex


@pytest_asyncio.fixture
async def seeded_db_dynamic(db_session):
    """전략 B 테스트용 데이터: 옷장 아이템 2개 + 카탈로그 상품 다수.

    외부 쇼핑몰 스타일의 상품 데이터:
    - 무신사/W컨셉 스타일 상품명, 브랜드, 가격대
    - 톤: spring_warm_light, autumn_warm_mute, summer_cool_soft 혼재
    """
    # 옷장 아이템 1: 코럴 핑크 블라우스 (상의)
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score)
        VALUES (:cid, :uid, 'https://img.user/coral-blouse.jpg', '블라우스', '#E8967C', 'spring_warm_light', 88.0, 85.0)
    """), {"cid": CLOSET_ITEM_ID_B1, "uid": USER_ID_B})

    # 옷장 아이템 2: 카멜 토트백 (가방)
    await db_session.execute(text("""
        INSERT INTO closet_items (id, user_id, image_url, category, dominant_color_hex, matched_tone_id, pcf_score, overall_score)
        VALUES (:cid, :uid, 'https://img.user/camel-tote.jpg', '토트백', '#C19A6B', 'autumn_warm_mute', 82.0, 78.0)
    """), {"cid": CLOSET_ITEM_ID_B2, "uid": USER_ID_B})

    # 카탈로그 상품 — 다양한 카테고리 (외부 쇼핑몰 스타일)
    await db_session.execute(text("""
        INSERT INTO products (id, name, brand, category, color_hex, tone_id, price, image_url, gender, age_group)
        VALUES
        ('ext-bottom-1', '와이드 코튼 팬츠 베이지', '디프로젝트', '면바지', '#D2B48C', 'autumn_warm_mute', 49000, 'https://image.musinsa.com/wide-pants.jpg', 'female', '20s'),
        ('ext-bottom-2', '핀턱 슬랙스 카키', '커렌트', '슬랙스', '#8B7355', 'autumn_warm_deep', 59000, 'https://image.musinsa.com/slacks-khaki.jpg', 'female', '20s'),
        ('ext-bottom-3', '플리츠 스커트 아이보리', '르메르', '스커트', '#FFFFF0', 'spring_warm_light', 68000, 'https://image.musinsa.com/skirt-ivory.jpg', 'female', '20s'),
        ('ext-shoes-1', '라운드토 메리제인 베이지', '레이첼콕스', '플랫슈즈', '#C8A882', 'autumn_warm_mute', 89000, 'https://image.musinsa.com/maryjane.jpg', 'female', '20s'),
        ('ext-shoes-2', '캔버스 스니커즈 크림', '컨버스', '스니커즈', '#FFFDD0', 'spring_warm_light', 69000, 'https://image.musinsa.com/sneakers-cream.jpg', 'female', '20s'),
        ('ext-shoes-3', '스웨이드 로퍼 탄', '바스', '로퍼', '#D2691E', 'autumn_warm_deep', 119000, 'https://image.musinsa.com/loafer-tan.jpg', 'female', '20s'),
        ('ext-outer-1', '린넨 블렌드 재킷 베이지', '코스', '자켓', '#F5DEB3', 'spring_warm_light', 159000, 'https://image.musinsa.com/jacket-beige.jpg', 'female', '20s'),
        ('ext-bag-1', '미니 크로스백 브라운', '마르니', '크로스백', '#8B4513', 'autumn_warm_deep', 45000, 'https://image.musinsa.com/crossbag.jpg', 'female', '20s'),
        ('ext-top-1', '오버핏 린넨 셔츠 크림', '포터리', '셔츠', '#FFFDD0', 'spring_warm_light', 55000, 'https://image.musinsa.com/shirt-cream.jpg', 'female', '20s'),
        ('ext-top-2', '리브 니트 탑 피치', '아크네', '니트', '#FFDAB9', 'spring_warm_bright', 79000, 'https://image.musinsa.com/knit-peach.jpg', 'female', '20s'),
        ('ext-acc-1', '스카프 페이즐리 코럴', '에르메스', '스카프', '#FF7F50', 'spring_warm_vivid', 35000, 'https://image.musinsa.com/scarf.jpg', 'female', '20s')
    """))

    await db_session.commit()

    # 피드 캐시 비우기 (전략 A 매칭 안 되게)
    import time as _time
    from app.services.feed_service import _feed_cache
    _feed_cache["outfits"] = []
    _feed_cache["item_map"] = {}
    _feed_cache["expires_at"] = _time.time() + 600

    yield db_session

    _feed_cache["outfits"] = None
    _feed_cache["item_map"] = None
    _feed_cache["expires_at"] = 0.0


class TestDynamicComboIntegration:
    """전략 B 동적 조합 통합 테스트 (외부 쇼핑몰 데이터 기반)."""

    @pytest.mark.asyncio
    async def test_single_item_fallback_to_dynamic(self, seeded_db_dynamic):
        """DB 매칭 0개 → 전략 B fallback 발동."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        assert "dynamic_combo" in result["strategy_used"]
        assert result["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_dynamic_combo_has_correct_structure(self, seeded_db_dynamic):
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        if result["total_count"] > 0:
            outfit = result["outfits"][0]
            assert outfit["source"] == "dynamic_combo"
            assert outfit["db_outfit_id"] is None
            assert "pcf" in outfit["scores"]
            assert "ch" in outfit["scores"]
            assert outfit["purchase_summary"]["my_items_count"] == 1

    @pytest.mark.asyncio
    async def test_dynamic_combo_closet_item_included(self, seeded_db_dynamic):
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        if result["total_count"] > 0:
            outfit = result["outfits"][0]
            closet_items_in_outfit = [it for it in outfit["items"] if it["source"] == "closet"]
            assert len(closet_items_in_outfit) == 1
            assert closet_items_in_outfit[0]["id"] == CLOSET_ITEM_ID_B1

    @pytest.mark.asyncio
    async def test_multi_item_direct_dynamic(self, seeded_db_dynamic):
        """복수 아이템(상의+가방) → 전략 B 직행, 하의+신발 매칭."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_ids=[CLOSET_ITEM_ID_B1, CLOSET_ITEM_ID_B2],
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        assert result["strategy_used"] == "dynamic_combo"
        assert result["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_multi_item_both_closet_items_included(self, seeded_db_dynamic):
        """복수 아이템 결과에 두 옷장 아이템 모두 포함."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_ids=[CLOSET_ITEM_ID_B1, CLOSET_ITEM_ID_B2],
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        if result["total_count"] > 0:
            outfit = result["outfits"][0]
            closet_ids = {it["id"] for it in outfit["items"] if it["source"] == "closet"}
            assert CLOSET_ITEM_ID_B1 in closet_ids
            assert CLOSET_ITEM_ID_B2 in closet_ids
            assert outfit["purchase_summary"]["my_items_count"] == 2

    @pytest.mark.asyncio
    async def test_dynamic_combo_sorted_by_score(self, seeded_db_dynamic):
        """결과가 스코어 내림차순으로 정렬됨."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        scores = [o["total_score"] for o in result["outfits"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_budget_max_respected(self, seeded_db_dynamic):
        """budget_max 설정 시 초과 조합 제외."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
            budget_max=60000,
        )
        for outfit in result["outfits"]:
            assert outfit["purchase_summary"]["purchase_total"] <= 60000

    @pytest.mark.asyncio
    async def test_limit_respected(self, seeded_db_dynamic):
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
            limit=2,
        )
        assert len(result["outfits"]) <= 2

    @pytest.mark.asyncio
    async def test_nonexistent_items_empty(self, seeded_db_dynamic):
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
        )
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_no_ids_returns_none_strategy(self, seeded_db_dynamic):
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
        )
        assert result["strategy_used"] == "none"
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_dynamic_combo_all_catalog_items_have_price(self, seeded_db_dynamic):
        """동적 조합의 카탈로그 아이템은 모두 가격 있음."""
        result = await match_outfits_for_closet_item(
            seeded_db_dynamic,
            closet_item_id=CLOSET_ITEM_ID_B1,
            user_id=USER_ID_B,
            user_tone_id="spring_warm_light",
            gender="female",
            age_group="20s",
        )
        for outfit in result["outfits"]:
            for it in outfit["items"]:
                if it["source"] == "catalog":
                    assert it.get("price") is not None
                    assert it["price"] > 0
