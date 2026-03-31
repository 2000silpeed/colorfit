"""하이브리드 카테고리 분류기 테스트."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.services.category_classifier import (
    classify_by_keyword,
    classify_product,
    LlmClassificationCache,
    _build_gemini_prompt,
    _parse_gemini_response,
    VALID_CATEGORIES,
    VALID_TPO,
    _CATEGORY_TO_GROUP,
)


class TestClassifyByKeyword:
    """1단계: 키워드 기반 분류."""

    def test_raw_category_priority(self):
        """네이버 raw_category가 키워드보다 우선."""
        result = classify_by_keyword("린넨 셔츠 원피스", raw_category3="니트", raw_category4="카디건")
        assert result["category"] == "가디건"
        assert result["group"] == "outer"

    def test_raw_category3_fallback(self):
        result = classify_by_keyword("패션 아이템", raw_category3="청바지")
        assert result["category"] == "청바지"
        assert result["group"] == "bottom"

    def test_keyword_match_basic(self):
        result = classify_by_keyword("여성 캐시미어 니트 브이넥")
        assert result["category"] == "니트"
        assert result["group"] == "top"

    def test_keyword_match_sweater(self):
        """풀오버 → 니트로 매핑 (기획서 예시)."""
        result = classify_by_keyword("워셔블 캐시미어 V넥 풀오버")
        assert result["category"] == "니트"

    def test_keyword_long_match_first(self):
        """긴 키워드 우선 매칭: 트렌치코트 > 코트."""
        result = classify_by_keyword("클래식 트렌치코트 베이지")
        assert result["category"] == "코트"

    def test_keyword_no_match(self):
        result = classify_by_keyword("여성 프리미엄 캐주얼 아이템")
        assert result is None

    def test_onepiece_priority_over_shirt(self):
        """원피스가 셔츠보다 먼저 매칭 (기획서 오분류 예시)."""
        result = classify_by_keyword("린넨 셔츠 원피스")
        # 원피스 키워드가 존재하면 원피스로 분류
        assert result["category"] == "원피스"

    def test_all_major_categories(self):
        """7개 대카테고리 모두 매칭 가능."""
        cases = [
            ("봄 니트", "top"),
            ("슬림핏 슬랙스", "bottom"),
            ("더블 코트", "outer"),
            ("플라워 원피스", "onepiece"),
            ("가죽 로퍼", "shoes"),
            ("캔버스 토트백", "bag"),
            ("실크 스카프", "acc"),
        ]
        for name, expected_group in cases:
            result = classify_by_keyword(name)
            assert result is not None, f"'{name}'이 매칭되지 않음"
            assert result["group"] == expected_group, f"'{name}': {result['group']} != {expected_group}"

    def test_case_insensitive(self):
        result = classify_by_keyword("BASIC 니트 SWEATER")
        assert result["category"] == "니트"

    def test_space_insensitive(self):
        result = classify_by_keyword("와이드 팬츠 린넨")
        assert result["category"] == "와이드팬츠"


class TestLlmClassificationCache:
    """LLM 분류 캐시."""

    def test_empty_cache(self, tmp_path):
        cache = LlmClassificationCache(tmp_path / "cache.json")
        assert len(cache) == 0
        assert cache.get("product_1") is None

    def test_put_and_get(self, tmp_path):
        cache = LlmClassificationCache(tmp_path / "cache.json")
        data = {"category": "니트", "silhouette": "regular", "formality": 3, "tpo": ["casual"], "gender": "female"}
        cache.put("product_1", data)
        assert cache.get("product_1") == data

    def test_save_and_reload(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        cache = LlmClassificationCache(cache_path)
        cache.put("p1", {"category": "니트"})
        cache.put("p2", {"category": "셔츠"})
        cache.save()

        cache2 = LlmClassificationCache(cache_path)
        assert len(cache2) == 2
        assert cache2.get("p1")["category"] == "니트"
        assert cache2.get("p2")["category"] == "셔츠"

    def test_put_batch(self, tmp_path):
        cache = LlmClassificationCache(tmp_path / "cache.json")
        batch = {
            "p1": {"category": "니트"},
            "p2": {"category": "셔츠"},
            "p3": {"category": "코트"},
        }
        cache.put_batch(batch)
        assert len(cache) == 3
        assert cache.get("p2")["category"] == "셔츠"


class TestParseGeminiResponse:
    """Gemini 응답 파싱 + 유효성 검증."""

    def test_valid_response(self):
        resp = json.dumps([{
            "product_id": "123",
            "category": "니트",
            "silhouette": "slim",
            "formality": 3,
            "tpo": ["office", "commute"],
            "gender": "female",
        }])
        results = _parse_gemini_response(resp)
        assert len(results) == 1
        assert results[0]["category"] == "니트"
        assert results[0]["tpo"] == ["office", "commute"]

    def test_markdown_wrapped(self):
        resp = '```json\n[{"product_id": "456", "category": "셔츠", "silhouette": "fitted", "formality": 4, "tpo": ["office"], "gender": "male"}]\n```'
        results = _parse_gemini_response(resp)
        assert len(results) == 1
        assert results[0]["category"] == "셔츠"

    def test_invalid_category_nullified(self):
        resp = json.dumps([{
            "product_id": "789",
            "category": "존재안함",
            "silhouette": "regular",
            "formality": 3,
            "tpo": ["casual"],
            "gender": "unisex",
        }])
        results = _parse_gemini_response(resp)
        assert results[0]["category"] is None

    def test_invalid_formality_defaults_to_3(self):
        resp = json.dumps([{
            "product_id": "100",
            "category": "니트",
            "silhouette": "regular",
            "formality": 99,
            "tpo": ["casual"],
            "gender": "unisex",
        }])
        results = _parse_gemini_response(resp)
        assert results[0]["formality"] == 3

    def test_invalid_tpo_defaults_to_casual(self):
        resp = json.dumps([{
            "product_id": "200",
            "category": "니트",
            "silhouette": "regular",
            "formality": 2,
            "tpo": ["invalid_tpo"],
            "gender": "female",
        }])
        results = _parse_gemini_response(resp)
        assert results[0]["tpo"] == ["casual"]

    def test_empty_response(self):
        assert _parse_gemini_response("no json here") == []

    def test_malformed_json(self):
        assert _parse_gemini_response("[{broken json}]") == []


class TestClassifyProduct:
    """하이브리드 분류 통합 테스트."""

    def test_keyword_hit(self):
        product = {"product_id": "1", "name": "캐시미어 니트 여성"}
        result = classify_product(product)
        assert result["category"] == "니트"
        assert result["source"] == "keyword"

    def test_raw_category_hit(self):
        product = {"product_id": "2", "name": "아무 이름", "raw_category3": "니트", "raw_category4": "카디건"}
        result = classify_product(product)
        assert result["category"] == "가디건"
        assert result["source"] == "raw_category"

    def test_llm_cache_hit(self, tmp_path):
        cache = LlmClassificationCache(tmp_path / "cache.json")
        cache.put("p99", {
            "category": "슬랙스",
            "silhouette": "slim",
            "formality": 4,
            "tpo": ["office"],
            "gender": "female",
        })
        product = {"product_id": "p99", "name": "여성 프리미엄 하이웨스트 아이템"}
        result = classify_product(product, cache=cache)
        assert result["category"] == "슬랙스"
        assert result["silhouette"] == "slim"
        assert result["source"] == "llm_cache"

    def test_unknown_fallback(self):
        product = {"product_id": "999", "name": "알 수 없는 아이템"}
        result = classify_product(product)
        assert result["category"] is None
        assert result["source"] == "unknown"

    def test_keyword_takes_priority_over_cache(self, tmp_path):
        """키워드 매칭이 성공하면 캐시를 조회하지 않는다."""
        cache = LlmClassificationCache(tmp_path / "cache.json")
        cache.put("p1", {"category": "코트"})
        product = {"product_id": "p1", "name": "여성 봄 니트"}
        result = classify_product(product, cache=cache)
        assert result["category"] == "니트"
        assert result["source"] == "keyword"


class TestBuildGeminiPrompt:
    def test_prompt_contains_items(self):
        items = [{"product_id": "1", "name": "테스트 상품", "raw_category3": "패션의류"}]
        prompt = _build_gemini_prompt(items)
        assert "테스트 상품" in prompt
        assert "product_id: 1" in prompt
        assert "니트" in prompt  # VALID_CATEGORIES에 포함


class TestCategoryToGroupMapping:
    def test_all_categories_have_group(self):
        """모든 VALID_CATEGORIES가 그룹에 매핑되어야 한다."""
        for cat in VALID_CATEGORIES:
            assert cat in _CATEGORY_TO_GROUP, f"'{cat}'에 대한 그룹 매핑 없음"

    def test_31_categories(self):
        """31개 카테고리 확인."""
        assert len(VALID_CATEGORIES) >= 31
