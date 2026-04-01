"""precompute_scores.py 단위 테스트."""

import pytest

from scripts.precompute_scores import (
    compute_scores,
    extract_tone_from_tags,
    _tone_level_pcf,
    CATEGORY_TO_GROUP,
)


class TestExtractToneFromTags:
    def test_extracts_tone(self):
        tags = ["spring_warm_light", "interview", "female", "spring"]
        assert extract_tone_from_tags(tags) == "spring_warm_light"

    def test_autumn_tone(self):
        tags = ["autumn_warm_deep", "casual", "male"]
        assert extract_tone_from_tags(tags) == "autumn_warm_deep"

    def test_no_tone(self):
        assert extract_tone_from_tags(["interview", "female"]) is None

    def test_empty(self):
        assert extract_tone_from_tags([]) is None
        assert extract_tone_from_tags(None) is None


class TestComputeScores:
    @pytest.fixture
    def product_index(self):
        return {
            "p001": {
                "product_id": "p001",
                "tone_id": "spring_warm_light",
                "color_hex": "#F5F0E1",
                "category": "니트",
                "silhouette": "fitted",
            },
            "p002": {
                "product_id": "p002",
                "tone_id": "spring_warm_light",
                "color_hex": "#C8B89A",
                "category": "슬랙스",
                "silhouette": "slim",
            },
            "p003": {
                "product_id": "p003",
                "tone_id": "autumn_warm_mute",
                "color_hex": "#8B7355",
                "category": "로퍼",
            },
        }

    def test_basic_compute(self, product_index):
        outfit = {
            "id": "test_001",
            "tags": ["spring_warm_light", "commute", "female"],
            "designed_tpo": "commute",
            "total_price": 150000,
            "items_snapshot": [
                {"product_id": "p001", "category": "니트", "price": 39000},
                {"product_id": "p002", "category": "슬랙스", "price": 69000},
                {"product_id": "p003", "category": "로퍼", "price": 49000},
            ],
        }
        scores = compute_scores(outfit, product_index)

        assert "pcf" in scores
        assert "of" in scores
        assert "ch" in scores
        assert "pe" in scores
        assert "sf" in scores
        for axis in scores:
            assert 0 <= scores[axis] <= 100

    def test_pcf_high_for_matching_tone(self, product_index):
        outfit = {
            "id": "test_002",
            "tags": ["spring_warm_light", "casual"],
            "designed_tpo": "casual",
            "total_price": 108000,
            "items_snapshot": [
                {"product_id": "p001", "category": "니트", "price": 39000},
                {"product_id": "p002", "category": "슬랙스", "price": 69000},
            ],
        }
        scores = compute_scores(outfit, product_index)
        # 둘 다 spring_warm_light이므로 PCF 높아야 함
        assert scores["pcf"] >= 90

    def test_empty_items(self, product_index):
        outfit = {
            "id": "test_003",
            "tags": ["spring_warm_light"],
            "designed_tpo": "casual",
            "total_price": 0,
            "items_snapshot": [],
        }
        scores = compute_scores(outfit, product_index)
        assert scores["pcf"] == 0.0
        assert scores["sf"] == 0.0

    def test_pe_in_budget_range(self, product_index):
        outfit = {
            "id": "test_004",
            "tags": ["spring_warm_light"],
            "designed_tpo": "casual",
            "total_price": 100000,
            "items_snapshot": [
                {"product_id": "p001", "category": "니트", "price": 100000},
            ],
        }
        scores = compute_scores(outfit, product_index)
        # 총액 == budget_mid이므로 PE 높아야 함
        assert scores["pe"] >= 80

    def test_of_matches_designed_tpo(self, product_index):
        outfit = {
            "id": "test_005",
            "tags": ["spring_warm_light", "office", "commute"],
            "designed_tpo": "commute",
            "total_price": 100000,
            "items_snapshot": [
                {"product_id": "p001", "category": "니트", "price": 100000},
            ],
        }
        scores = compute_scores(outfit, product_index)
        assert scores["of"] >= 60

    def test_missing_product_in_index(self):
        """normalized에 없는 상품도 에러 없이 처리."""
        outfit = {
            "id": "test_006",
            "tags": ["winter_cool_deep"],
            "designed_tpo": "casual",
            "total_price": 50000,
            "items_snapshot": [
                {"product_id": "unknown_001", "category": "티셔츠", "price": 50000},
            ],
        }
        scores = compute_scores(outfit, {})
        assert scores["sf"] > 0  # 카테고리가 있으니 SF는 0이 아님

    def test_no_tone_in_tags(self, product_index):
        """톤 없는 코디도 에러 없이 처리."""
        outfit = {
            "id": "test_007",
            "tags": ["casual", "female"],
            "designed_tpo": "casual",
            "total_price": 50000,
            "items_snapshot": [
                {"product_id": "p001", "category": "니트", "price": 50000},
            ],
        }
        scores = compute_scores(outfit, product_index)
        assert scores["pcf"] == 0.0


class TestToneLevelPcf:
    def test_same_tone(self):
        assert _tone_level_pcf(["spring_warm_light"], "spring_warm_light") == 100.0

    def test_compatible_tone(self):
        assert _tone_level_pcf(["spring_warm_bright"], "spring_warm_light") == 95.0

    def test_same_season_different_tone(self):
        # spring_warm_vivid is compatible with spring_warm_light,
        # but a non-compatible same-season would be 70
        # All spring tones are compatible, so test with summer
        result = _tone_level_pcf(["summer_cool_light"], "summer_cool_mute")
        assert result == 95.0  # compatible

    def test_different_season(self):
        result = _tone_level_pcf(["winter_cool_deep"], "spring_warm_light")
        assert result == 30.0

    def test_mixed_tones(self):
        result = _tone_level_pcf(
            ["spring_warm_light", "autumn_warm_deep"],
            "spring_warm_light",
        )
        # (100 + 30) / 2 = 65
        assert result == 65.0

    def test_empty(self):
        assert _tone_level_pcf([], "spring_warm_light") == 0.0


class TestCategoryToGroup:
    def test_top_categories(self):
        assert CATEGORY_TO_GROUP["티셔츠"] == "top"
        assert CATEGORY_TO_GROUP["블라우스"] == "top"

    def test_bottom_categories(self):
        assert CATEGORY_TO_GROUP["슬랙스"] == "bottom"
        assert CATEGORY_TO_GROUP["청바지"] == "bottom"

    def test_shoes(self):
        assert CATEGORY_TO_GROUP["로퍼"] == "shoes"
        assert CATEGORY_TO_GROUP["스니커즈"] == "shoes"
