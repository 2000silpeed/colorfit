"""generate_outfits.py 유닛 테스트 v2.

검증 대상: 포멀도, 가격비율(3배), 금지카테고리, 중복방지, 레시피 선택,
           성별 키워드 필터, 계절별 금지 카테고리.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_outfits import (
    DEFAULT_FORMALITY,
    MALE_KEYWORDS,
    FEMALE_KEYWORDS,
    build_item_pool,
    make_outfit_id,
    pick_optional_items,
    pick_required_items,
    validate_forbidden,
    validate_formality,
    validate_price_ratio,
    generate_outfits_for_slot,
)


def _item(pid: str, category: str, price: int = 30000,
          formality: int | None = None, gender: str = "female",
          name: str | None = None) -> dict:
    return {
        "product_id": pid,
        "name": name or f"테스트 {category}",
        "category": category,
        "formality": formality if formality is not None else DEFAULT_FORMALITY.get(category, 3),
        "price": price,
        "gender": gender,
        "image_url": "https://example.com/test.jpg",
    }


class TestValidateForbidden:
    def test_no_forbidden(self):
        items = [_item("1", "셔츠"), _item("2", "슬랙스")]
        assert validate_forbidden(items, ["후드", "스니커즈"]) is True

    def test_has_forbidden(self):
        items = [_item("1", "후드"), _item("2", "슬랙스")]
        assert validate_forbidden(items, ["후드", "스니커즈"]) is False

    def test_empty_forbidden(self):
        items = [_item("1", "후드")]
        assert validate_forbidden(items, []) is True

    def test_season_forbidden_overlay(self):
        items = [_item("1", "패딩"), _item("2", "슬랙스")]
        season_forbidden = ["코트", "패딩", "부츠", "가디건"]
        combined = ["후드"] + season_forbidden
        assert validate_forbidden(items, combined) is False


class TestValidateFormality:
    def test_within_range(self):
        items = [_item("1", "셔츠", formality=4), _item("2", "슬랙스", formality=4)]
        assert validate_formality(items, [3, 5]) is True

    def test_deviation_over_2(self):
        items = [_item("1", "후드", formality=1), _item("2", "슬랙스", formality=4)]
        assert validate_formality(items, [1, 5]) is False

    def test_deviation_exactly_2(self):
        items = [_item("1", "니트", formality=2), _item("2", "슬랙스", formality=4)]
        assert validate_formality(items, [2, 5]) is True

    def test_outside_range(self):
        items = [_item("1", "후드", formality=1)]
        assert validate_formality(items, [3, 5]) is False


class TestValidatePriceRatio:
    def test_within_3x(self):
        items = [_item("1", "셔츠", price=20000), _item("2", "슬랙스", price=60000)]
        assert validate_price_ratio(items) is True

    def test_over_3x(self):
        items = [_item("1", "셔츠", price=20000), _item("2", "슬랙스", price=60001)]
        assert validate_price_ratio(items) is False

    def test_single_item(self):
        items = [_item("1", "셔츠", price=10000)]
        assert validate_price_ratio(items) is True

    def test_zero_price_ignored(self):
        items = [_item("1", "셔츠", price=0), _item("2", "슬랙스", price=30000)]
        assert validate_price_ratio(items) is True


class TestBuildItemPool:
    def test_gender_filter(self):
        items = [
            _item("1", "셔츠", gender="female"),
            _item("2", "셔츠", gender="male"),
            _item("3", "니트", gender="unisex"),
        ]
        pool = build_item_pool(items, "female")
        assert len(pool.get("셔츠", [])) == 1
        assert pool["셔츠"][0]["product_id"] == "1"
        assert len(pool.get("니트", [])) == 1

    def test_male_pool(self):
        items = [
            _item("1", "셔츠", gender="female"),
            _item("2", "셔츠", gender="male"),
        ]
        pool = build_item_pool(items, "male")
        assert len(pool.get("셔츠", [])) == 1
        assert pool["셔츠"][0]["product_id"] == "2"

    def test_keyword_filter_excludes_opposite_gender(self):
        items = [
            _item("1", "스니커즈", gender="unisex", name="남성용 스니커즈 블랙"),
            _item("2", "스니커즈", gender="unisex", name="유니섹스 스니커즈 화이트"),
        ]
        pool = build_item_pool(items, "female")
        assert len(pool.get("스니커즈", [])) == 1
        assert pool["스니커즈"][0]["product_id"] == "2"

    def test_keyword_filter_male_excludes_female(self):
        items = [
            _item("1", "청바지", gender="unisex", name="여성 슬림 청바지"),
            _item("2", "청바지", gender="unisex", name="데일리 청바지"),
        ]
        pool = build_item_pool(items, "male")
        assert len(pool.get("청바지", [])) == 1
        assert pool["청바지"][0]["product_id"] == "2"


class TestPickRequiredItems:
    def test_required_slots(self):
        pool = {
            "셔츠": [_item("1", "셔츠")],
            "슬랙스": [_item("2", "슬랙스")],
        }
        recipe = {
            "required": [["셔츠", "블라우스"], ["슬랙스"]],
            "gender": "female",
        }
        result = pick_required_items(recipe, pool)
        assert result is not None
        assert len(result) == 2

    def test_missing_category(self):
        pool = {"셔츠": [_item("1", "셔츠")]}
        recipe = {
            "required": [["셔츠"], ["슬랙스"]],
            "gender": "female",
        }
        result = pick_required_items(recipe, pool)
        assert result is None

    def test_required_sets(self):
        pool = {
            "원피스": [_item("1", "원피스")],
            "니트": [_item("2", "니트")],
            "스커트": [_item("3", "스커트")],
            "힐": [_item("4", "힐")],
        }
        recipe = {
            "required_sets": [
                [["니트", "블라우스"], ["스커트", "슬랙스"], ["힐", "로퍼"]],
                [["원피스"], ["힐", "로퍼"]],
            ],
            "gender": "female",
        }
        result = pick_required_items(recipe, pool)
        assert result is not None
        assert len(result) >= 2


class TestPickOptionalItems:
    def test_probability_1(self):
        pool = {"스니커즈": [_item("1", "스니커즈")]}
        recipe = {
            "optional": [{"categories": ["스니커즈"], "probability": 1.0}],
        }
        result = pick_optional_items(recipe, pool)
        assert len(result) == 1

    def test_probability_0(self):
        pool = {"스니커즈": [_item("1", "스니커즈")]}
        recipe = {
            "optional": [{"categories": ["스니커즈"], "probability": 0.0}],
        }
        result = pick_optional_items(recipe, pool)
        assert len(result) == 0

    def test_missing_category(self):
        pool = {}
        recipe = {
            "optional": [{"categories": ["스니커즈"], "probability": 1.0}],
        }
        result = pick_optional_items(recipe, pool)
        assert len(result) == 0


class TestGenerateOutfitsForSlot:
    def test_dedup(self):
        pool = {
            "셔츠": [_item("1", "셔츠")],
            "슬랙스": [_item("2", "슬랙스")],
            "로퍼": [_item("3", "로퍼")],
        }
        recipe = {
            "gender": "female",
            "tpo": "interview",
            "moods": ["classic"],
            "required": [["셔츠"], ["슬랙스"], ["로퍼"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [3, 5],
        }
        seen = set()
        outfits = generate_outfits_for_slot(
            recipe, pool, "spring_warm_light", "spring", "20s", [], seen, target_count=5
        )
        assert len(outfits) == 1

    def test_outfit_fields_with_season(self):
        pool = {
            "셔츠": [_item(f"s{i}", "셔츠", price=20000 + i * 1000) for i in range(10)],
            "슬랙스": [_item(f"p{i}", "슬랙스", price=30000 + i * 1000) for i in range(10)],
            "로퍼": [_item(f"r{i}", "로퍼", price=40000 + i * 1000) for i in range(10)],
        }
        recipe = {
            "gender": "female",
            "tpo": "commute",
            "moods": ["classic", "minimal"],
            "required": [["셔츠"], ["슬랙스"], ["로퍼"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [3, 5],
        }
        seen = set()
        outfits = generate_outfits_for_slot(
            recipe, pool, "spring_warm_light", "fall", "30s", [], seen, target_count=3
        )
        assert len(outfits) >= 1

        o = outfits[0]
        assert o["gender"] == "female"
        assert o["designed_tpo"] == "commute"
        assert o["designed_season"] == "fall"
        assert "fall" in o["tags"]
        assert o["is_complete_outfit"] is True
        assert len(o["items_snapshot"]) == 3

    def test_season_forbidden_blocks_items(self):
        pool = {
            "티셔츠": [_item("1", "티셔츠")],
            "숏팬츠": [_item("2", "숏팬츠")],
            "스니커즈": [_item("3", "스니커즈")],
        }
        recipe = {
            "gender": "male",
            "tpo": "travel",
            "moods": ["casual"],
            "required": [["티셔츠"], ["숏팬츠"], ["스니커즈"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [1, 2],
        }
        seen = set()
        winter_forbidden = ["샌들", "숏팬츠", "크롭탑", "탱크탑"]
        outfits = generate_outfits_for_slot(
            recipe, pool, "spring_warm_light", "winter", "20s", winter_forbidden, seen, target_count=3
        )
        assert len(outfits) == 0


class TestMakeOutfitId:
    def test_format_with_season(self):
        oid = make_outfit_id("female", "spring_warm_light", "interview", "spring", "20s", 1)
        assert oid == "outfit_f_springwa_interview_sp_20_001"

    def test_male_winter(self):
        oid = make_outfit_id("male", "winter_cool_deep", "event", "winter", "40plus", 10)
        assert oid == "outfit_m_winterco_event_wi_40_010"
