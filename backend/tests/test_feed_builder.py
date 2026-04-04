"""Hard Filter 체인 테스트.

각 필터별 통과/탈락 케이스 + 체인 통합 테스트.
"""

import pytest

from app.services.feed_builder import (
    apply_hard_filters,
    calculate_soft_score,
    h1_gender,
    h2_budget,
    h3_season,
    h4_tpo,
    h5_brand,
    h6_llm_quality,
    h7_tone,
    h8_style_filter,
    rerank,
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
        assert h2_budget(100_000, 50_000, 150_000) is True

    def test_at_max_passes(self):
        assert h2_budget(100_000, None, 100_000) is True

    def test_over_max_fails(self):
        assert h2_budget(100_001, None, 100_000) is False

    def test_under_min_fails(self):
        assert h2_budget(30_000, 50_000, 150_000) is False

    def test_at_min_passes(self):
        assert h2_budget(50_000, 50_000, 150_000) is True

    def test_none_total_price_passes(self):
        assert h2_budget(None, 50_000, 100_000) is True

    def test_none_budget_passes(self):
        assert h2_budget(100_000, None, None) is True

    def test_zero_budget_passes(self):
        assert h2_budget(100_000, 0, 0) is True


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

    def test_empty_brands_passes(self):
        assert h5_brand([]) is True

    def test_none_brands_passes(self):
        assert h5_brand([None, None]) is True


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
            {"category": "레깅스", "group": "bottom", "silhouette": "slim"},
            {"category": "코트", "group": "outer", "silhouette": None},
            {"category": "힐", "group": "shoes", "silhouette": None},
        ]
        assert h8_style_filter(items) is False

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

    def test_h8_rejection(self):
        items = [
            {"brand": "유니클로", "tone_id": "spring_warm_light",
             "category": "레깅스", "group": "bottom", "silhouette": "slim"},
            {"brand": "COS", "tone_id": "spring_warm_bright",
             "category": "코트", "group": "outer", "silhouette": None},
            {"brand": "무신사 스탠다드", "tone_id": "spring_warm_light",
             "category": "힐", "group": "shoes", "silhouette": None},
        ]
        passed, reason = apply_hard_filters(
            _make_outfit(), _make_user(), items, current_month=4,
        )
        assert passed is False
        assert reason == "H8_style_filter"

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


# ---------------------------------------------------------------------------
# Soft Score 계산
# ---------------------------------------------------------------------------

class TestCalculateSoftScore:
    def test_default_weights(self):
        scores = {"pcf": 80.0, "of": 70.0, "ch": 60.0, "pe": 90.0, "sf": 85.0}
        # 80*0.25 + 70*0.20 + 60*0.15 + 90*0.15 + 85*0.25
        # = 20 + 14 + 9 + 13.5 + 21.25 = 77.75
        assert calculate_soft_score(scores) == 77.75

    def test_all_100(self):
        scores = {"pcf": 100, "of": 100, "ch": 100, "pe": 100, "sf": 100}
        assert calculate_soft_score(scores) == 100.0

    def test_all_zero(self):
        scores = {"pcf": 0, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        assert calculate_soft_score(scores) == 0.0

    def test_none_scores(self):
        assert calculate_soft_score(None) == 0.0

    def test_empty_scores(self):
        assert calculate_soft_score({}) == 0.0

    def test_partial_scores(self):
        scores = {"pcf": 100.0, "sf": 100.0}
        # 100*0.25 + 0*0.20 + 0*0.15 + 0*0.15 + 100*0.25 = 50.0
        assert calculate_soft_score(scores) == 50.0

    def test_weight_overrides(self):
        scores = {"pcf": 100, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        result = calculate_soft_score(scores, weight_overrides={"pcf": 1.0})
        assert result == 100.0

    def test_weight_overrides_partial(self):
        scores = {"pcf": 80, "of": 60, "ch": 50, "pe": 70, "sf": 90}
        overrides = {"pcf": 0.40}
        # 80*0.40 + 60*0.20 + 50*0.15 + 70*0.15 + 90*0.25
        # = 32 + 12 + 7.5 + 10.5 + 22.5 = 84.5
        assert calculate_soft_score(scores, overrides) == 84.5


# ---------------------------------------------------------------------------
# 리랭킹
# ---------------------------------------------------------------------------

def _make_scored_outfit(
    outfit_id: str,
    soft_score: float,
    *,
    is_complete: bool = False,
    tone: str | None = None,
    main_item: str | None = None,
) -> dict:
    return {
        "id": outfit_id,
        "soft_score": soft_score,
        "is_complete_outfit": is_complete,
        "dominant_tone": tone,
        "main_item_id": main_item,
    }


class TestRerank:
    def test_basic_sort_by_score(self):
        outfits = [
            _make_scored_outfit("a", 60.0),
            _make_scored_outfit("b", 80.0),
            _make_scored_outfit("c", 70.0),
        ]
        result = rerank(outfits)
        assert [o["id"] for o in result] == ["b", "c", "a"]

    def test_complete_outfit_bonus(self):
        outfits = [
            _make_scored_outfit("a", 80.0, is_complete=False),
            _make_scored_outfit("b", 78.0, is_complete=True),
        ]
        result = rerank(outfits)
        # b: 78 + 3 = 81 > a: 80
        assert result[0]["id"] == "b"
        assert result[0]["final_score"] == 81.0

    def test_dislike_exclusion(self):
        outfits = [
            _make_scored_outfit("a", 90.0),
            _make_scored_outfit("b", 80.0),
            _make_scored_outfit("c", 70.0),
        ]
        result = rerank(outfits, disliked_ids={"a", "c"})
        assert len(result) == 1
        assert result[0]["id"] == "b"

    def test_tone_diversity_limit_3(self):
        outfits = [
            _make_scored_outfit("a", 90.0, tone="spring_warm_light"),
            _make_scored_outfit("b", 85.0, tone="spring_warm_light"),
            _make_scored_outfit("c", 80.0, tone="spring_warm_light"),
            _make_scored_outfit("d", 75.0, tone="spring_warm_light"),
            _make_scored_outfit("e", 70.0, tone="summer_cool_light"),
        ]
        result = rerank(outfits)
        assert len(result) == 4
        ids = [o["id"] for o in result]
        assert "d" not in ids
        assert "e" in ids

    def test_main_item_dedup(self):
        outfits = [
            _make_scored_outfit("a", 90.0, main_item="item_1"),
            _make_scored_outfit("b", 85.0, main_item="item_1"),
            _make_scored_outfit("c", 80.0, main_item="item_2"),
        ]
        result = rerank(outfits)
        assert len(result) == 2
        assert [o["id"] for o in result] == ["a", "c"]

    def test_personalization_positive(self):
        outfits = [
            _make_scored_outfit("a", 70.0),
            _make_scored_outfit("b", 75.0),
        ]
        result = rerank(outfits, personalization={"a": 10.0})
        # a: 70+10=80, b: 75
        assert result[0]["id"] == "a"
        assert result[0]["final_score"] == 80.0

    def test_personalization_negative(self):
        outfits = [
            _make_scored_outfit("a", 80.0),
            _make_scored_outfit("b", 75.0),
        ]
        result = rerank(outfits, personalization={"a": -10.0})
        # a: 80-10=70, b: 75
        assert result[0]["id"] == "b"

    def test_personalization_clamped(self):
        outfits = [_make_scored_outfit("a", 50.0)]
        result = rerank(outfits, personalization={"a": 99.0})
        assert result[0]["final_score"] == 60.0

    def test_personalization_clamped_negative(self):
        outfits = [_make_scored_outfit("a", 50.0)]
        result = rerank(outfits, personalization={"a": -99.0})
        assert result[0]["final_score"] == 40.0

    def test_limit(self):
        outfits = [_make_scored_outfit(f"o{i}", float(i)) for i in range(300)]
        result = rerank(outfits, limit=200)
        assert len(result) == 200

    def test_none_tone_no_diversity_limit(self):
        outfits = [
            _make_scored_outfit("a", 90.0, tone=None),
            _make_scored_outfit("b", 80.0, tone=None),
            _make_scored_outfit("c", 70.0, tone=None),
            _make_scored_outfit("d", 60.0, tone=None),
        ]
        result = rerank(outfits)
        assert len(result) == 4

    def test_none_main_item_no_dedup(self):
        outfits = [
            _make_scored_outfit("a", 90.0, main_item=None),
            _make_scored_outfit("b", 80.0, main_item=None),
        ]
        result = rerank(outfits)
        assert len(result) == 2

    def test_empty_input(self):
        assert rerank([]) == []

    def test_combined_rules(self):
        """완성도 가산 + 톤 다양성 + 메인아이템 중복 + dislike 동시 적용."""
        outfits = [
            _make_scored_outfit("a", 90.0, tone="t1", main_item="m1"),
            _make_scored_outfit("b", 88.0, tone="t1", main_item="m1"),  # m1 중복
            _make_scored_outfit("c", 85.0, tone="t1", main_item="m2"),
            _make_scored_outfit("d", 83.0, tone="t1", main_item="m3"),
            _make_scored_outfit("e", 80.0, tone="t1", main_item="m4"),  # t1 4번째
            _make_scored_outfit("f", 75.0, tone="t2", main_item="m5", is_complete=True),
            _make_scored_outfit("g", 70.0, tone="t2", main_item="m6"),
        ]
        result = rerank(outfits, disliked_ids={"g"})
        ids = [o["id"] for o in result]
        assert "b" not in ids  # 메인아이템 중복
        assert "e" not in ids  # 톤 다양성 초과
        assert "g" not in ids  # dislike
        assert ids == ["a", "c", "d", "f"]
        assert result[3]["final_score"] == 78.0  # f: 75+3
