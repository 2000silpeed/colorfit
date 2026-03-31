"""generate_outfits.py 유닛 테스트.

검증 대상: 포멀도, 가격비율, 금지카테고리, 중복방지, 레시피 선택 로직.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_outfits import (
    DEFAULT_FORMALITY,
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
          formality: int | None = None, gender: str = "female") -> dict:
    return {
        "product_id": pid,
        "name": f"테스트 {category}",
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
    def test_within_5x(self):
        items = [_item("1", "셔츠", price=10000), _item("2", "슬랙스", price=50000)]
        assert validate_price_ratio(items) is True

    def test_over_5x(self):
        items = [_item("1", "셔츠", price=10000), _item("2", "슬랙스", price=50001)]
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
        }
        recipe = {
            "required_sets": [
                [["니트", "블라우스"], ["스커트", "슬랙스"]],
                [["원피스"]],
            ],
            "gender": "female",
        }
        result = pick_required_items(recipe, pool)
        assert result is not None
        assert len(result) >= 1


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
        }
        recipe = {
            "gender": "female",
            "tpo": "interview",
            "moods": ["classic"],
            "required": [["셔츠"], ["슬랙스"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [3, 5],
        }
        seen = set()
        outfits = generate_outfits_for_slot(recipe, pool, "spring_warm_light", seen, target_count=5)
        assert len(outfits) == 1

    def test_outfit_fields(self):
        pool = {
            "셔츠": [_item(f"s{i}", "셔츠", price=20000 + i * 1000) for i in range(10)],
            "슬랙스": [_item(f"p{i}", "슬랙스", price=30000 + i * 1000) for i in range(10)],
        }
        recipe = {
            "gender": "female",
            "tpo": "commute",
            "moods": ["classic", "minimal"],
            "required": [["셔츠"], ["슬랙스"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [3, 5],
        }
        seen = set()
        outfits = generate_outfits_for_slot(recipe, pool, "spring_warm_light", seen, target_count=3)
        assert len(outfits) >= 1

        o = outfits[0]
        assert o["gender"] == "female"
        assert o["designed_tpo"] == "commute"
        assert o["designed_moods"] == ["classic", "minimal"]
        assert o["is_complete_outfit"] is True
        assert o["total_price"] > 0
        assert len(o["item_ids"]) == 2
        assert len(o["items_snapshot"]) == 2


class TestMakeOutfitId:
    def test_format(self):
        oid = make_outfit_id("female", "spring_warm_light", "interview", 1)
        assert oid == "outfit_f_springwa_interview_001"

    def test_male(self):
        oid = make_outfit_id("male", "winter_cool_deep", "event", 10)
        assert oid == "outfit_m_winterco_event_010"
