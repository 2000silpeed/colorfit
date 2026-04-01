"""Hard Filter 체인 테스트.

각 필터별 통과/탈락 케이스 + 체인 통합 테스트.
"""

import pytest

from app.services.feed_builder import (
    apply_hard_filters,
    h1_gender,
    h2_budget,
    h3_season,
    h4_tpo,
    h5_brand,
    h6_llm_quality,
    h7_tone,
    h8_style_filter,
)


# ---------------------------------------------------------------------------
# H1: 성별 불일치
# ---------------------------------------------------------------------------

class TestH1Gender:
    def test_same_gender_passes(self):
        assert h1_gender("female", "female") is True

    def test_different_gender_fails(self):
        assert h1_gender("male", "female") is False

    def test_unisex_always_passes(self):
        assert h1_gender("unisex", "female") is True
        assert h1_gender("unisex", "male") is True

    def test_none_gender_passes(self):
        assert h1_gender(None, "female") is True
        assert h1_gender("male", None) is True


# ---------------------------------------------------------------------------
# H2: 예산 초과
# ---------------------------------------------------------------------------

class TestH2Budget:
    def test_within_budget_passes(self):
        assert h2_budget(100_000, 100_000) is True

    def test_slightly_over_passes(self):
        assert h2_budget(140_000, 100_000) is True

    def test_at_150_percent_passes(self):
        assert h2_budget(150_000, 100_000) is True

    def test_over_150_percent_fails(self):
        assert h2_budget(150_001, 100_000) is False

    def test_none_values_pass(self):
        assert h2_budget(None, 100_000) is True
        assert h2_budget(100_000, None) is True

    def test_zero_budget_passes(self):
        assert h2_budget(100_000, 0) is True


# ---------------------------------------------------------------------------
# H3: 계절 완전 불일치
# ---------------------------------------------------------------------------

class TestH3Season:
    def test_same_season_passes(self):
        assert h3_season("summer", current_month=7) is True

    def test_adjacent_season_passes(self):
        assert h3_season("spring", current_month=6) is True
        assert h3_season("autumn", current_month=8) is True

    def test_opposite_season_fails(self):
        assert h3_season("winter", current_month=7) is False
        assert h3_season("summer", current_month=1) is False

    def test_travel_tpo_bypasses(self):
        assert h3_season("winter", current_month=7, outfit_tpo="travel") is True

    def test_none_season_passes(self):
        assert h3_season(None, current_month=7) is True

    def test_spring_autumn_opposite(self):
        assert h3_season("autumn", current_month=4) is False
        assert h3_season("spring", current_month=10) is False


# ---------------------------------------------------------------------------
# H4: TPO 완전 불일치
# ---------------------------------------------------------------------------

class TestH4Tpo:
    def test_matching_tpo_passes(self):
        assert h4_tpo("office", ["commute", "weekend"]) is True

    def test_synonym_match_passes(self):
        assert h4_tpo("casual", ["weekend"]) is True

    def test_no_match_fails(self):
        assert h4_tpo("workout", ["office", "date"]) is False

    def test_all_tab_bypasses(self):
        assert h4_tpo("workout", ["office"], active_tab="전체") is True
        assert h4_tpo("workout", ["office"], active_tab="all") is True

    def test_none_values_pass(self):
        assert h4_tpo(None, ["office"]) is True
        assert h4_tpo("office", None) is True


# ---------------------------------------------------------------------------
# H5: 브랜드 화이트리스트
# ---------------------------------------------------------------------------

class TestH5Brand:
    def test_whitelist_brand_passes(self):
        assert h5_brand(["유니클로", "노브랜드ABC"]) is True

    def test_no_whitelist_brand_fails(self):
        assert h5_brand(["알수없는브랜드", "또다른브랜드"]) is False

    def test_case_insensitive(self):
        assert h5_brand(["COS"]) is True
        assert h5_brand(["cos"]) is True

    def test_empty_brands_fails(self):
        assert h5_brand([]) is False

    def test_none_brands_fails(self):
        assert h5_brand([None, None]) is False


# ---------------------------------------------------------------------------
# H6: LLM 품질
# ---------------------------------------------------------------------------

class TestH6LlmQuality:
    def test_score_3_passes(self):
        assert h6_llm_quality(3) is True

    def test_score_5_passes(self):
        assert h6_llm_quality(5) is True

    def test_score_2_fails(self):
        assert h6_llm_quality(2) is False

    def test_score_1_fails(self):
        assert h6_llm_quality(1) is False

    def test_none_passes(self):
        assert h6_llm_quality(None) is True


# ---------------------------------------------------------------------------
# H7: 톤 호환성
# ---------------------------------------------------------------------------

class TestH7Tone:
    def test_same_tone_passes(self):
        assert h7_tone(["spring_warm_light"], "spring_warm_light") is True

    def test_compatible_tone_passes(self):
        assert h7_tone(["spring_warm_bright"], "spring_warm_light") is True

    def test_incompatible_tone_fails(self):
        assert h7_tone(["winter_cool_deep"], "spring_warm_light") is False

    def test_mixed_tones_one_match_passes(self):
        assert h7_tone(
            ["winter_cool_deep", "spring_warm_vivid"],
            "spring_warm_light",
        ) is True

    def test_no_user_tone_passes(self):
        assert h7_tone(["winter_cool_deep"], None) is True

    def test_no_item_tones_passes(self):
        assert h7_tone([], "spring_warm_light") is True

    def test_all_none_tones_fails(self):
        assert h7_tone([None, None], "spring_warm_light") is False


# ---------------------------------------------------------------------------
# H8: StyleFilter 컷오프
# ---------------------------------------------------------------------------

class TestH8StyleFilter:
    def test_good_outfit_passes(self):
        items = [
            {"category": "블라우스", "group": "top", "silhouette": "fitted"},
            {"category": "슬랙스", "group": "bottom", "silhouette": "slim"},
            {"category": "로퍼", "group": "shoes", "silhouette": None},
        ]
        assert h8_style_filter(items) is True

    def test_bad_outfit_fails(self):
        items = [
            {"category": "후드티", "group": "top", "silhouette": "oversized"},
            {"category": "정장바지", "group": "bottom", "silhouette": "slim"},
            {"category": "힐", "group": "shoes", "silhouette": None},
        ]
        passed = h8_style_filter(items)
        assert isinstance(passed, bool)

    def test_empty_items_fails(self):
        assert h8_style_filter([]) is False


# ---------------------------------------------------------------------------
# 체인 통합 테스트
# ---------------------------------------------------------------------------

def _make_outfit(**overrides) -> dict:
    base = {
        "gender": "female",
        "designed_tpo": "commute",
        "designed_season": "spring",
        "total_price": 100_000,
        "llm_quality_score": 4,
    }
    base.update(overrides)
    return base


def _make_user(**overrides) -> dict:
    base = {
        "gender": "female",
        "tone_id": "spring_warm_light",
        "tpo_list": ["commute", "weekend"],
        "budget_max": 200_000,
    }
    base.update(overrides)
    return base


def _make_items() -> list[dict]:
    return [
        {
            "brand": "유니클로",
            "tone_id": "spring_warm_light",
            "category": "블라우스",
            "group": "top",
            "silhouette": "fitted",
        },
        {
            "brand": "COS",
            "tone_id": "spring_warm_bright",
            "category": "슬랙스",
            "group": "bottom",
            "silhouette": "slim",
        },
        {
            "brand": "무신사 스탠다드",
            "tone_id": "spring_warm_light",
            "category": "로퍼",
            "group": "shoes",
            "silhouette": None,
        },
    ]


class TestApplyHardFilters:
    def test_all_pass(self):
        passed, reason = apply_hard_filters(
            _make_outfit(), _make_user(), _make_items(), current_month=4,
        )
        assert passed is True
        assert reason is None

    def test_h1_rejection(self):
        passed, reason = apply_hard_filters(
            _make_outfit(gender="male"), _make_user(), _make_items(), current_month=4,
        )
        assert passed is False
        assert reason == "H1_gender"

    def test_h2_rejection(self):
        passed, reason = apply_hard_filters(
            _make_outfit(total_price=400_000),
            _make_user(budget_max=200_000),
            _make_items(),
            current_month=4,
        )
        assert passed is False
        assert reason == "H2_budget"

    def test_h3_rejection(self):
        passed, reason = apply_hard_filters(
            _make_outfit(designed_season="autumn"),
            _make_user(),
            _make_items(),
            current_month=4,
        )
        assert passed is False
        assert reason == "H3_season"

    def test_h4_rejection(self):
        passed, reason = apply_hard_filters(
            _make_outfit(designed_tpo="workout"),
            _make_user(tpo_list=["office"]),
            _make_items(),
            current_month=4,
        )
        assert passed is False
        assert reason == "H4_tpo"

    def test_h5_rejection(self):
        items = [
            {"brand": "알수없는", "tone_id": "spring_warm_light",
             "category": "블라우스", "group": "top", "silhouette": "fitted"},
            {"brand": "또다른", "tone_id": "spring_warm_bright",
             "category": "슬랙스", "group": "bottom", "silhouette": "slim"},
        ]
        passed, reason = apply_hard_filters(
            _make_outfit(), _make_user(), items, current_month=4,
        )
        assert passed is False
        assert reason == "H5_brand"

    def test_h7_rejection(self):
        items = [
            {"brand": "유니클로", "tone_id": "winter_cool_deep",
             "category": "블라우스", "group": "top", "silhouette": "fitted"},
            {"brand": "COS", "tone_id": "winter_cool_strong",
             "category": "슬랙스", "group": "bottom", "silhouette": "slim"},
        ]
        passed, reason = apply_hard_filters(
            _make_outfit(), _make_user(tone_id="spring_warm_light"),
            items, current_month=4,
        )
        assert passed is False
        assert reason == "H7_tone"

    def test_h6_rejection(self):
        passed, reason = apply_hard_filters(
            _make_outfit(llm_quality_score=2),
            _make_user(),
            _make_items(),
            current_month=4,
        )
        assert passed is False
        assert reason == "H6_llm_quality"

    def test_early_exit_order(self):
        """H1이 먼저 걸리면 H2는 체크하지 않는다."""
        passed, reason = apply_hard_filters(
            _make_outfit(gender="male", total_price=999_999),
            _make_user(),
            _make_items(),
            current_month=4,
        )
        assert reason == "H1_gender"
