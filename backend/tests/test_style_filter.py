"""StyleFilter 테스트.

기획서 섹션 6.6 기준.
통과 코디, 탈락 코디, 55점 경계, detect_category 3단계 폴백 검증.
"""

import pytest

from app.services.style_filter import (
    STYLE_FILTER_THRESHOLD,
    detect_category,
    filter_outfit,
)
from app.services.category_classifier import LlmClassificationCache


# ---------------------------------------------------------------------------
# detect_category 테스트
# ---------------------------------------------------------------------------


class TestDetectCategory:
    """detect_category 3단계 폴백 검증."""

    def test_keyword_match(self):
        """상품명 키워드로 카테고리 감지."""
        result = detect_category("오버사이즈 니트 스웨터")
        assert result["category"] == "니트"
        assert result["group"] == "top"
        assert result["source"] == "keyword"

    def test_raw_category_match(self):
        """네이버 raw_category로 카테고리 감지."""
        result = detect_category("ABC 상품", category3="슬랙스")
        assert result["category"] == "슬랙스"
        assert result["group"] == "bottom"
        assert result["source"] == "raw_category"

    def test_llm_cache_match(self, tmp_path):
        """키워드 실패 시 LLM 캐시에서 감지."""
        cache = LlmClassificationCache(tmp_path / "cache.json")
        cache.put("prod_001", {
            "category": "가디건",
            "silhouette": "regular",
            "formality": 3,
            "tpo": ["casual"],
            "gender": "female",
        })

        result = detect_category(
            "알 수 없는 상품명",
            product_id="prod_001",
            cache=cache,
        )
        assert result["category"] == "가디건"
        assert result["group"] == "outer"
        assert result["source"] == "llm_cache"
        assert result["silhouette"] == "regular"

    def test_unknown_fallback(self):
        """키워드도 캐시도 없으면 unknown."""
        result = detect_category("완전히 알 수 없는 상품 XYZ")
        assert result["category"] is None
        assert result["source"] == "unknown"

    def test_keyword_with_llm_metadata(self, tmp_path):
        """키워드 매칭 성공 시 LLM 캐시에서 메타데이터(silhouette, formality) 보충."""
        cache = LlmClassificationCache(tmp_path / "cache.json")
        cache.put("prod_002", {
            "category": "니트",
            "silhouette": "oversized",
            "formality": 3,
        })

        result = detect_category(
            "오버사이즈 니트",
            product_id="prod_002",
            cache=cache,
        )
        assert result["category"] == "니트"
        assert result["source"] == "keyword"
        assert result["silhouette"] == "oversized"
        assert result["formality"] == 3

    def test_onepiece_priority(self):
        """'셔츠 원피스'에서 원피스가 우선 매칭."""
        result = detect_category("셔츠 원피스 롱 드레스")
        assert result["category"] == "원피스"
        assert result["group"] == "onepiece"


# ---------------------------------------------------------------------------
# filter_outfit 테스트
# ---------------------------------------------------------------------------


class TestFilterOutfit:
    """filter_outfit 3축 가중합 + 55점 탈락 기준 검증."""

    def test_pass_formal_outfit(self):
        """블라우스+슬랙스+로퍼 → 궁합 좋고 포멀도 일치 → 통과."""
        items = [
            {"category": "블라우스", "group": "top", "silhouette": "fitted"},
            {"category": "슬랙스", "group": "bottom", "silhouette": "slim"},
            {"category": "로퍼", "group": "shoes", "silhouette": None},
        ]
        passed, score = filter_outfit(items)
        assert passed is True
        assert score >= 80.0

    def test_pass_casual_outfit(self):
        """티셔츠+청바지+스니커즈 → 캐주얼 통일 → 통과."""
        items = [
            {"category": "티셔츠", "group": "top", "silhouette": "regular"},
            {"category": "청바지", "group": "bottom", "silhouette": "slim"},
            {"category": "스니커즈", "group": "shoes", "silhouette": None},
        ]
        passed, score = filter_outfit(items)
        assert passed is True
        assert score >= 60.0

    def test_fail_sporty_formal_mix(self):
        """레깅스+코트+힐 → 스포츠+포멀 극단 편차 → 탈락."""
        items = [
            {"category": "레깅스", "group": "bottom", "silhouette": "slim"},
            {"category": "코트", "group": "outer", "silhouette": None},
            {"category": "힐", "group": "shoes", "silhouette": None},
        ]
        passed, score = filter_outfit(items)
        # 레깅스(1) + 코트(5) + 힐(5) → 포멀도 stdev ≈ 1.89 → 포멀도 점수 ~24
        assert passed is False
        assert score < STYLE_FILTER_THRESHOLD

    def test_fail_extreme_mismatch(self):
        """레깅스+정장재킷+하이힐 → 극단적 불일치 → 확실한 탈락."""
        items = [
            {"category": "레깅스", "group": "bottom", "silhouette": "slim"},
            {"category": "자켓", "group": "outer", "silhouette": "fitted"},
            {"category": "힐", "group": "shoes", "silhouette": None},
        ]
        passed, score = filter_outfit(items)
        # 레깅스(1) + 자켓(4) + 힐(5) → 포멀도 stdev ≈ 1.70 → 포멀도 점수 ~32
        assert score < 60.0

    def test_boundary_55(self):
        """55점 경계: 55점 이상이면 통과, 미만이면 탈락."""
        # 경계값 동작 확인 — 정확히 55점은 통과해야 함
        items_good = [
            {"category": "니트", "group": "top", "silhouette": "regular"},
            {"category": "청바지", "group": "bottom", "silhouette": "slim"},
            {"category": "스니커즈", "group": "shoes", "silhouette": None},
        ]
        passed, score = filter_outfit(items_good)
        assert passed is True
        assert score >= STYLE_FILTER_THRESHOLD

    def test_empty_items(self):
        """빈 아이템 → 탈락."""
        passed, score = filter_outfit([])
        assert passed is False
        assert score == 0.0

    def test_no_category_items(self):
        """카테고리 없는 아이템만 → 탈락."""
        items = [
            {"category": None, "group": "", "silhouette": None},
        ]
        passed, score = filter_outfit(items)
        assert passed is False
        assert score == 0.0

    def test_silhouette_y_line_bonus(self):
        """오버사이즈 상의 + 슬림 하의 (Y라인) → 실루엣 점수 높음."""
        items = [
            {"category": "니트", "group": "top", "silhouette": "oversized"},
            {"category": "청바지", "group": "bottom", "silhouette": "slim"},
            {"category": "스니커즈", "group": "shoes", "silhouette": None},
        ]
        passed_y, score_y = filter_outfit(items)

        items_bad_sil = [
            {"category": "니트", "group": "top", "silhouette": "oversized"},
            {"category": "청바지", "group": "bottom", "silhouette": "wide"},
            {"category": "스니커즈", "group": "shoes", "silhouette": None},
        ]
        _, score_bad = filter_outfit(items_bad_sil)

        assert score_y > score_bad

    def test_single_item(self):
        """아이템 1개 → 카테고리 궁합 70, 실루엣 70, 포멀도 100 → 통과."""
        items = [
            {"category": "니트", "group": "top", "silhouette": "regular"},
        ]
        passed, score = filter_outfit(items)
        assert passed is True
        assert score >= 70.0

    def test_threshold_constant(self):
        """임계값이 55점인지 확인."""
        assert STYLE_FILTER_THRESHOLD == 55.0
