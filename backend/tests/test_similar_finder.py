"""유사 상품 매칭 서비스 테스트.

순수 함수 테스트 + DB 통합 테스트.
"""

import pytest
import pytest_asyncio
from sqlalchemy import insert

from app.services.similar_finder import (
    _color_similarity,
    _price_similarity,
    _normalize_name,
    classify_match_type,
    compute_similarity,
    find_similar_products,
)
from tests.conftest import products_table


# ── 순수 함수 테스트 ──


class TestColorSimilarity:
    def test_identical_colors(self):
        assert _color_similarity("#FF0000", "#FF0000") == 1.0

    def test_opposite_colors(self):
        sim = _color_similarity("#000000", "#FFFFFF")
        assert sim == pytest.approx(0.0, abs=0.01)

    def test_similar_colors_high_score(self):
        sim = _color_similarity("#FF0000", "#FF1010")
        assert sim > 0.94

    def test_different_colors_low_score(self):
        sim = _color_similarity("#FF0000", "#0000FF")
        assert sim < 0.5


class TestPriceSimilarity:
    def test_identical_prices(self):
        assert _price_similarity(10000, 10000) == 1.0

    def test_double_price(self):
        assert _price_similarity(10000, 20000) == 0.5

    def test_zero_price(self):
        assert _price_similarity(0, 10000) == 0.0

    def test_both_zero(self):
        assert _price_similarity(0, 0) == 0.0


class TestNormalizeName:
    def test_basic(self):
        assert _normalize_name("Nike Air Max 90") == "nikeairmax90"

    def test_korean(self):
        assert _normalize_name("나이키 에어맥스 90") == "나이키에어맥스90"

    def test_special_chars(self):
        assert _normalize_name("[특가] 나이키-에어맥스!") == "특가나이키에어맥스"


class TestClassifyMatchType:
    def test_exact_same_name_brand(self):
        assert classify_match_type(
            "Nike Air Max 90", "Nike",
            "Nike Air Max 90", "Nike",
        ) == "exact"

    def test_exact_case_insensitive(self):
        assert classify_match_type(
            "nike air max 90", "NIKE",
            "Nike Air Max 90", "nike",
        ) == "exact"

    def test_similar_different_name(self):
        assert classify_match_type(
            "Nike Air Max 90", "Nike",
            "Nike Air Force 1", "Nike",
        ) == "similar"

    def test_similar_different_brand(self):
        assert classify_match_type(
            "Air Max 90", "Nike",
            "Air Max 90", "Adidas",
        ) == "similar"

    def test_none_name(self):
        assert classify_match_type(None, "Nike", "Nike Air", "Nike") == "similar"

    def test_none_brand(self):
        assert classify_match_type("Air Max", None, "Air Max", "Nike") == "similar"


class TestComputeSimilarity:
    def test_identical_product(self):
        score = compute_similarity("#FF0000", 30000, "#FF0000", 30000)
        assert score == 1.0

    def test_weights(self):
        """색상 가중치 0.6 + 가격 가중치 0.4 검증."""
        color_only = compute_similarity("#FF0000", 10000, "#FF0000", 20000)
        price_only = compute_similarity("#FF0000", 10000, "#0000FF", 10000)
        # 색상 동일 + 가격 차이 → 색상 가중치가 높으므로 점수가 더 높아야 함
        assert color_only > price_only


# ── DB 통합 테스트 ──


SOURCE_PRODUCT = {
    "id": "src-001",
    "name": "나이키 에어맥스 90",
    "brand": "Nike",
    "category": "sneakers",
    "color_hex": "#F5F5DC",
    "price": 130000,
    "tone_id": "spring_warm_light",
    "mall_name": "무신사",
}

CANDIDATE_PRODUCTS = [
    {
        "id": "cand-001",
        "name": "나이키 에어맥스 90",
        "brand": "Nike",
        "category": "sneakers",
        "color_hex": "#F5F5DC",
        "price": 120000,
        "mall_name": "29CM",
    },
    {
        "id": "cand-002",
        "name": "뉴발란스 993",
        "brand": "New Balance",
        "category": "sneakers",
        "color_hex": "#F0E8D0",
        "price": 140000,
        "mall_name": "무신사",
    },
    {
        "id": "cand-003",
        "name": "아디다스 슈퍼스타",
        "brand": "Adidas",
        "category": "sneakers",
        "color_hex": "#0000FF",
        "price": 90000,
        "mall_name": "무신사",
    },
    {
        "id": "cand-004",
        "name": "자라 블라우스",
        "brand": "Zara",
        "category": "blouse",
        "color_hex": "#F5F5DC",
        "price": 59000,
        "mall_name": "자라",
    },
    {
        "id": "cand-005",
        "name": "나이키 덩크 로우",
        "brand": "Nike",
        "category": "sneakers",
        "color_hex": "#E8DCC8",
        "price": 135000,
        "mall_name": "한정판",
    },
    {
        "id": "cand-no-color",
        "name": "색상 없음",
        "brand": "None",
        "category": "sneakers",
        "color_hex": None,
        "price": 100000,
        "mall_name": "기타",
    },
]


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """테스트용 상품 데이터 시딩."""
    all_products = [SOURCE_PRODUCT] + CANDIDATE_PRODUCTS
    for p in all_products:
        await db_session.execute(insert(products_table).values(**p))
    await db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_find_similar_returns_top5(seeded_db):
    results = await find_similar_products(seeded_db, "src-001", limit=5)
    assert len(results) <= 5
    assert len(results) > 0


@pytest.mark.asyncio
async def test_find_similar_excludes_different_category(seeded_db):
    """다른 카테고리(blouse)는 후보에서 제외."""
    results = await find_similar_products(seeded_db, "src-001")
    ids = [r["product"].id for r in results]
    assert "cand-004" not in ids


@pytest.mark.asyncio
async def test_find_similar_excludes_null_color(seeded_db):
    """color_hex가 None인 상품은 후보에서 제외."""
    results = await find_similar_products(seeded_db, "src-001")
    ids = [r["product"].id for r in results]
    assert "cand-no-color" not in ids


@pytest.mark.asyncio
async def test_find_similar_sorted_by_similarity(seeded_db):
    results = await find_similar_products(seeded_db, "src-001")
    similarities = [r["similarity"] for r in results]
    assert similarities == sorted(similarities, reverse=True)


@pytest.mark.asyncio
async def test_find_similar_exact_match_detected(seeded_db):
    """동일 상품 다른 판매처는 exact로 분류."""
    results = await find_similar_products(seeded_db, "src-001")
    exact_items = [r for r in results if r["match_type"] == "exact"]
    assert len(exact_items) >= 1
    assert exact_items[0]["product"].id == "cand-001"


@pytest.mark.asyncio
async def test_find_similar_nonexistent_product(seeded_db):
    results = await find_similar_products(seeded_db, "nonexistent")
    assert results == []


@pytest.mark.asyncio
async def test_find_similar_limit(seeded_db):
    results = await find_similar_products(seeded_db, "src-001", limit=2)
    assert len(results) <= 2
