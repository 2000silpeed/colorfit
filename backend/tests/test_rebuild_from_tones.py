"""rebuild_from_tones.py 단위 테스트."""

import json
import pytest
from pathlib import Path

from scripts.rebuild_from_tones import (
    strip_html,
    extract_brand,
    normalize_item,
    process_tone,
    load_brand_whitelist,
)


WHITELIST = {"무신사 스탠다드", "유니클로", "나이키", "빈폴레이디스", "로엠", "폴햄"}


class TestStripHtml:
    def test_removes_bold_tags(self):
        assert strip_html("린넨 <b>아이보리</b> 가디건") == "린넨 아이보리 가디건"

    def test_removes_multiple_tags(self):
        assert strip_html("<b>A</b> <i>B</i>") == "A B"

    def test_no_tags(self):
        assert strip_html("일반 텍스트") == "일반 텍스트"

    def test_empty_string(self):
        assert strip_html("") == ""


class TestExtractBrand:
    def test_api_brand_field(self):
        item = {"brand": "로엠", "title": "로엠 가디건", "maker": "이랜드"}
        assert extract_brand(item, WHITELIST) == "로엠"

    def test_title_first_token(self):
        item = {"brand": "", "title": "나이키 에어맥스 운동화", "maker": ""}
        assert extract_brand(item, WHITELIST) == "나이키"

    def test_title_multi_token(self):
        item = {"brand": "", "title": "무신사 스탠다드 슬랙스", "maker": ""}
        assert extract_brand(item, WHITELIST) == "무신사 스탠다드"

    def test_fallback_to_maker(self):
        item = {"brand": "", "title": "여성 브이넥 니트", "maker": "이랜드"}
        assert extract_brand(item, WHITELIST) == "이랜드"

    def test_no_brand(self):
        item = {"brand": "", "title": "여성 브이넥 니트", "maker": ""}
        assert extract_brand(item, WHITELIST) is None


class TestNormalizeItem:
    def test_basic_normalization(self):
        item = {
            "productId": "123",
            "title": "린넨 <b>아이보리</b> 가디건",
            "brand": "테스트",
            "link": "https://example.com",
            "image": "https://img.com/a.jpg",
            "lprice": "25800",
            "mallName": "테스트몰",
            "maker": "",
            "category1": "패션의류",
            "category2": "여성의류",
            "category3": "니트",
            "category4": "카디건",
        }
        result = normalize_item(item, "spring_warm_light", WHITELIST)

        assert result["product_id"] == "123"
        assert result["name"] == "린넨 아이보리 가디건"
        assert result["brand"] == "테스트"
        assert result["price"] == 25800
        assert result["tone_id"] == "spring_warm_light"
        assert result["category"] is None
        assert result["color_hex"] is None
        assert result["raw_category3"] == "니트"

    def test_empty_price(self):
        item = {
            "productId": "456",
            "title": "테스트",
            "brand": "",
            "link": "",
            "image": "",
            "lprice": "",
            "mallName": "",
            "maker": "",
        }
        result = normalize_item(item, "summer_cool_light", WHITELIST)
        assert result["price"] is None


class TestProcessTone:
    def test_deduplication(self, tmp_path):
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        items = [
            {"productId": "1", "title": "상품A", "brand": "", "link": "", "image": "",
             "lprice": "1000", "mallName": "", "maker": ""},
            {"productId": "1", "title": "상품A 중복", "brand": "", "link": "", "image": "",
             "lprice": "1000", "mallName": "", "maker": ""},
            {"productId": "2", "title": "상품B", "brand": "", "link": "", "image": "",
             "lprice": "2000", "mallName": "", "maker": ""},
        ]
        raw_file = raw_dir / "test_tone.json"
        raw_file.write_text(json.dumps({"items": items}), encoding="utf-8")

        import scripts.rebuild_from_tones as module
        original_raw_dir = module.RAW_DIR
        module.RAW_DIR = raw_dir
        try:
            result = process_tone("test_tone", WHITELIST)
            assert result["item_count"] == 2
            assert result["duplicates_removed"] == 1
        finally:
            module.RAW_DIR = original_raw_dir

    def test_missing_file(self, tmp_path):
        import scripts.rebuild_from_tones as module
        original_raw_dir = module.RAW_DIR
        module.RAW_DIR = tmp_path / "nonexistent"
        try:
            result = process_tone("missing_tone", WHITELIST)
            assert result["item_count"] == 0
        finally:
            module.RAW_DIR = original_raw_dir
