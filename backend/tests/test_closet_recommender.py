"""역방향 추천 서비스 테스트.

보유 옷 기반 TPO별 추천 로직 검증.
"""

import pytest
import pytest_asyncio
from sqlalchemy import insert

from app.services.closet_recommender import (
    _tone_compatible,
    _color_harmony_score,
    _compute_recommendation_score,
    _match_reason,
    recommend_for_closet_item,
    COMPLEMENTARY_CATEGORIES,
    TPO_LABELS,
)
from tests.conftest import products_table


# ── 순수 함수 테스트 ──


class TestToneCompatible:
    def test_exact_match(self):
        assert _tone_compatible("spring_warm_light", "spring_warm_light") is True

    def test_compatible_tone(self):
        assert _tone_compatible("spring_warm_bright", "spring_warm_light") is True

    def test_incompatible_tone(self):
        assert _tone_compatible("winter_cool_deep", "spring_warm_light") is False

    def test_none_tone(self):
        assert _tone_compatible(None, "spring_warm_light") is False


class TestColorHarmonyScore:
    def test_identical_colors(self):
        score = _color_harmony_score("#FF0000", "#FF0000")
        assert score == 1.0

    def test_returns_between_0_and_1(self):
        score = _color_harmony_score("#FF0000", "#00FF00")
        assert 0.0 <= score <= 1.0

    def test_similar_colors_high(self):
        score = _color_harmony_score("#F5F5DC", "#F0E8D0")
        assert score > 0.8


class TestComputeRecommendationScore:
    def test_tone_match_boosts_score(self):
        """톤 호환 상품이 더 높은 점수."""

        class MockProduct:
            tone_id = "spring_warm_light"
            color_hex = "#F5F5DC"
            price = 50000

        class MockProductBad:
            tone_id = "winter_cool_deep"
            color_hex = "#F5F5DC"
            price = 50000

        good = _compute_recommendation_score("#F5F5DC", MockProduct(), "spring_warm_light")
        bad = _compute_recommendation_score("#F5F5DC", MockProductBad(), "spring_warm_light")
        assert good > bad

    def test_returns_between_0_and_1(self):
        class MockProduct:
            tone_id = "spring_warm_light"
            color_hex = "#FF0000"
            price = 100000

        score = _compute_recommendation_score("#0000FF", MockProduct(), "winter_cool_deep")
        assert 0.0 <= score <= 1.0


class TestComplementaryCategories:
    def test_top_recommends_bottoms(self):
        cats = COMPLEMENTARY_CATEGORIES["상의"]
        assert "하의" in cats

    def test_bottom_recommends_tops(self):
        cats = COMPLEMENTARY_CATEGORIES["하의"]
        assert "상의" in cats

    def test_dress_recommends_outer(self):
        cats = COMPLEMENTARY_CATEGORIES["원피스"]
        assert "아우터" in cats


# ── DB 통합 테스트 ──

TEST_PRODUCTS = [
    {
        "id": "rec-top-001",
        "name": "린넨 셔츠",
        "brand": "유니클로",
        "category": "상의",
        "color_hex": "#F5F5DC",
        "tone_id": "spring_warm_light",
        "price": 39000,
        "mall_name": "무신사",
        "mall_url": "https://example.com/1",
        "image_url": "https://example.com/img1.jpg",
        "formality": 3,
    },
    {
        "id": "rec-bottom-001",
        "name": "와이드 팬츠",
        "brand": "자라",
        "category": "하의",
        "color_hex": "#E8DCC8",
        "tone_id": "spring_warm_bright",
        "price": 59000,
        "mall_name": "자라",
        "mall_url": "https://example.com/2",
        "image_url": "https://example.com/img2.jpg",
        "formality": 3,
    },
    {
        "id": "rec-bottom-002",
        "name": "캐주얼 조거팬츠",
        "brand": "나이키",
        "category": "하의",
        "color_hex": "#333333",
        "tone_id": "winter_cool_deep",
        "price": 45000,
        "mall_name": "나이키",
        "mall_url": "https://example.com/3",
        "image_url": "https://example.com/img3.jpg",
        "formality": 1,
    },
    {
        "id": "rec-outer-001",
        "name": "트렌치코트",
        "brand": "H&M",
        "category": "아우터",
        "color_hex": "#C4A882",
        "tone_id": "autumn_warm_mute",
        "price": 89000,
        "mall_name": "H&M",
        "mall_url": "https://example.com/4",
        "image_url": "https://example.com/img4.jpg",
        "formality": 4,
    },
    {
        "id": "rec-shoe-001",
        "name": "로퍼",
        "brand": "탠디",
        "category": "신발",
        "color_hex": "#8B4513",
        "tone_id": "autumn_warm_deep",
        "price": 120000,
        "mall_name": "탠디",
        "mall_url": "https://example.com/5",
        "image_url": "https://example.com/img5.jpg",
        "formality": 4,
    },
    {
        "id": "rec-bottom-formal",
        "name": "슬랙스",
        "brand": "지오다노",
        "category": "하의",
        "color_hex": "#2F4F4F",
        "tone_id": "winter_cool_strong",
        "price": 49000,
        "mall_name": "무신사",
        "mall_url": "https://example.com/6",
        "image_url": "https://example.com/img6.jpg",
        "formality": 5,
    },
]


@pytest_asyncio.fixture
async def seeded_db(db_session):
    for p in TEST_PRODUCTS:
        await db_session.execute(insert(products_table).values(**p))
    await db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_recommend_returns_tpo_groups(seeded_db):
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
    )
    assert len(results) > 0
    for r in results:
        assert r["tpo"] in TPO_LABELS
        assert len(r["items"]) > 0


@pytest.mark.asyncio
async def test_recommend_complementary_categories(seeded_db):
    """상의 기준 → 하의/아우터/신발/가방 카테고리만 추천."""
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
    )
    all_items = []
    for r in results:
        all_items.extend(r["items"])

    categories = {item["category"] for item in all_items}
    assert "상의" not in categories


@pytest.mark.asyncio
async def test_recommend_respects_tpo_filter(seeded_db):
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
        tpo_list=["commute"],
    )
    assert len(results) <= 1
    if results:
        assert results[0]["tpo"] == "commute"


@pytest.mark.asyncio
async def test_recommend_limit_per_tpo(seeded_db):
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
        limit_per_tpo=2,
    )
    for r in results:
        assert len(r["items"]) <= 2


@pytest.mark.asyncio
async def test_recommend_items_have_required_fields(seeded_db):
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
    )
    for r in results:
        for item in r["items"]:
            assert "id" in item
            assert "similarity" in item
            assert "match_reason" in item
            assert item["similarity"] >= 0


@pytest.mark.asyncio
async def test_recommend_sorted_by_score(seeded_db):
    results = await recommend_for_closet_item(
        db=seeded_db,
        source_color_hex="#F5F5DC",
        source_category="상의",
        user_tone_id="spring_warm_light",
    )
    for r in results:
        scores = [item["similarity"] for item in r["items"]]
        assert scores == sorted(scores, reverse=True)
