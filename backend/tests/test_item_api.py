"""Task 3.2 — 아이템 API 테스트.

GET /api/item/{id}, GET /api/item/{id}/similar
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.product import Product


client = TestClient(app)


def _mock_product(**overrides):
    defaults = dict(
        id="p1",
        name="린넨 블라우스",
        brand="무신사 스탠다드",
        category="블라우스",
        color_hex="#F0E0D0",
        tone_id="spring_warm_light",
        price=39900,
        mall_name="무신사",
        mall_url="https://musinsa.com/p1",
        image_url="https://img.musinsa.com/p1.jpg",
        gender="female",
        silhouette="regular",
        formality=3,
        tags=None,
        last_observed_at=None,
    )
    defaults.update(overrides)
    m = MagicMock(spec=Product)
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


# ── GET /api/item/{id} ──


class TestGetItemDetail:
    @patch("app.routers.item.get_db")
    def test_item_found(self, mock_get_db):
        product = _mock_product()
        session = AsyncMock()
        session.get.return_value = product
        # 판매처 가격 조회용
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [
            _mock_product(id="p1", mall_name="무신사", price=39900, mall_url="https://musinsa.com/p1"),
            _mock_product(id="p1b", mall_name="W컨셉", price=42000, mall_url="https://wconcept.com/p1"),
        ]
        session.execute.return_value = result_mock

        async def _override():
            yield session
        mock_get_db.return_value = _override()
        app.dependency_overrides[mock_get_db] = _override

        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "p1"
        assert data["name"] == "린넨 블라우스"
        assert data["brand"] == "무신사 스탠다드"
        assert len(data["price_entries"]) == 2
        assert data["price_entries"][0]["is_lowest"] is True
        assert data["price_entries"][0]["price"] <= data["price_entries"][1]["price"]

        app.dependency_overrides.clear()

    @patch("app.routers.item.get_db")
    def test_item_not_found(self, mock_get_db):
        session = AsyncMock()
        session.get.return_value = None

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/nonexistent")
        assert resp.status_code == 404

        app.dependency_overrides.clear()

    @patch("app.routers.item.get_db")
    def test_item_no_brand_single_entry(self, mock_get_db):
        product = _mock_product(brand=None)
        session = AsyncMock()
        session.get.return_value = product

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["price_entries"]) == 1
        assert data["price_entries"][0]["is_lowest"] is True

        app.dependency_overrides.clear()


# ── GET /api/item/{id}/similar ──


class TestGetSimilarItems:
    @patch("app.routers.item.find_similar_products")
    @patch("app.routers.item.get_db")
    def test_similar_found(self, mock_get_db, mock_find):
        source = _mock_product()
        session = AsyncMock()
        session.get.return_value = source

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        mock_find.return_value = [
            {
                "product": _mock_product(id="p2", name="린넨 셔츠", price=35000),
                "similarity": 0.85,
                "match_type": "similar",
            },
            {
                "product": _mock_product(id="p3", name="린넨 블라우스", price=42000, mall_name="W컨셉"),
                "similarity": 0.92,
                "match_type": "exact",
            },
        ]

        resp = client.get("/api/item/p1/similar")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_id"] == "p1"
        assert len(data["similar"]) == 2
        assert data["similar"][0]["similarity"] == 85.0
        assert data["similar"][0]["match_type"] == "similar"
        assert data["similar"][1]["match_type"] == "exact"

        app.dependency_overrides.clear()

    @patch("app.routers.item.get_db")
    def test_similar_item_not_found(self, mock_get_db):
        session = AsyncMock()
        session.get.return_value = None

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/nonexistent/similar")
        assert resp.status_code == 404

        app.dependency_overrides.clear()

    @patch("app.routers.item.find_similar_products")
    @patch("app.routers.item.get_db")
    def test_similar_limit_param(self, mock_get_db, mock_find):
        source = _mock_product()
        session = AsyncMock()
        session.get.return_value = source

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        mock_find.return_value = []

        resp = client.get("/api/item/p1/similar?limit=3")
        assert resp.status_code == 200
        mock_find.assert_called_once_with(session, "p1", limit=3)

        app.dependency_overrides.clear()

    def test_similar_limit_over_20_rejected(self):
        resp = client.get("/api/item/p1/similar?limit=100")
        assert resp.status_code == 422

    def test_similar_limit_zero_rejected(self):
        resp = client.get("/api/item/p1/similar?limit=0")
        assert resp.status_code == 422

    def test_similar_limit_negative_rejected(self):
        resp = client.get("/api/item/p1/similar?limit=-1")
        assert resp.status_code == 422


# ── 판매처 가격 정렬 테스트 ──


class TestPriceEntries:
    @patch("app.routers.item.get_db")
    def test_price_entries_sorted_ascending(self, mock_get_db):
        product = _mock_product()
        session = AsyncMock()
        session.get.return_value = product

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [
            _mock_product(id="p1c", mall_name="SSG", price=45000, mall_url="https://ssg.com/p1"),
            _mock_product(id="p1", mall_name="무신사", price=39900, mall_url="https://musinsa.com/p1"),
            _mock_product(id="p1b", mall_name="W컨셉", price=42000, mall_url="https://wconcept.com/p1"),
        ]
        session.execute.return_value = result_mock

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/p1")
        data = resp.json()
        prices = [e["price"] for e in data["price_entries"]]
        assert prices == sorted(prices)
        assert data["price_entries"][0]["is_lowest"] is True
        assert all(e["is_lowest"] is False for e in data["price_entries"][1:])

        app.dependency_overrides.clear()

    @patch("app.routers.item.get_db")
    def test_duplicate_mall_deduplication(self, mock_get_db):
        product = _mock_product()
        session = AsyncMock()
        session.get.return_value = product

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [
            _mock_product(id="p1", mall_name="무신사", price=39900, mall_url="https://musinsa.com/p1"),
            _mock_product(id="p1d", mall_name="무신사", price=38000, mall_url="https://musinsa.com/p1d"),
        ]
        session.execute.return_value = result_mock

        async def _override():
            yield session
        from app.db.session import get_db
        app.dependency_overrides[get_db] = _override

        resp = client.get("/api/item/p1")
        data = resp.json()
        assert len(data["price_entries"]) == 1
        assert data["price_entries"][0]["price"] == 38000

        app.dependency_overrides.clear()


# ── 스키마 검증 ──


class TestItemSchemas:
    def test_similarity_percentage(self):
        from app.schemas.item import SimilarProductResponse
        item = SimilarProductResponse(
            id="p1", similarity=85.0, match_type="similar",
        )
        assert item.similarity == 85.0

    def test_price_entry_default(self):
        from app.schemas.item import PriceEntry
        entry = PriceEntry(mall_name="무신사", price=30000, mall_url="https://x.com")
        assert entry.is_lowest is False
