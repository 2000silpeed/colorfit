"""Virtual Try-On API 테스트.

Gemini API를 mock하여 착장 이미지 생성 플로우를 테스트한다.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


TEST_USER_ID = str(uuid.uuid4())
TEST_OUTFIT_ID = "outfit_001"
TEST_CLOSET_ITEM_ID = str(uuid.uuid4())
FAKE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest_asyncio.fixture
async def seed_data(db_session):
    """테스트용 outfit + product + closet_item 데이터 시드."""
    await db_session.execute(
        _text(
            "INSERT INTO products (id, name, image_url) VALUES "
            "(:id1, :n1, :u1), (:id2, :n2, :u2)"
        ),
        {
            "id1": "prod_001", "n1": "화이트 셔츠",
            "u1": "https://example.com/shirt.jpg",
            "id2": "prod_002", "n2": "네이비 슬랙스",
            "u2": "https://example.com/pants.jpg",
        },
    )

    await db_session.execute(
        _text(
            "INSERT INTO outfits (id, item_ids) VALUES (:oid, :items)"
        ),
        {"oid": TEST_OUTFIT_ID, "items": '["prod_001","prod_002"]'},
    )

    await db_session.execute(
        _text(
            "INSERT INTO closet_items (id, user_id, image_url, category) "
            "VALUES (:cid, :uid, :curl, :cat)"
        ),
        {
            "cid": TEST_CLOSET_ITEM_ID,
            "uid": TEST_USER_ID,
            "curl": "https://example.com/my_jacket.jpg",
            "cat": "outer",
        },
    )

    await db_session.commit()
    return db_session


def _text(sql: str):
    from sqlalchemy import text
    return text(sql)


def _mock_gemini_response():
    """Gemini API 응답 mock 객체."""
    inline_data = MagicMock()
    inline_data.data = FAKE_IMAGE_BYTES

    part = MagicMock()
    part.inline_data = inline_data

    content = MagicMock()
    content.parts = [part]

    candidate = MagicMock()
    candidate.content = content

    response = MagicMock()
    response.candidates = [candidate]
    return response


def _mock_gemini_empty_response():
    """이미지 없는 Gemini 응답."""
    response = MagicMock()
    response.candidates = []
    return response


class TestTryonGenerate:
    """POST /api/tryon/generate 테스트."""

    @pytest.mark.asyncio
    async def test_generate_success(self, db_session, seed_data):
        """정상적인 착장 이미지 생성."""
        mock_response = _mock_gemini_response()
        item_urls = ["https://example.com/shirt.jpg", "https://example.com/pants.jpg"]

        with (
            patch("app.services.virtual_tryon._fetch_image_bytes", new_callable=AsyncMock) as mock_fetch,
            patch("app.services.virtual_tryon._get_item_image_urls", new_callable=AsyncMock) as mock_items,
            patch("app.services.virtual_tryon.genai") as mock_genai,
        ):
            mock_fetch.return_value = FAKE_IMAGE_BYTES
            mock_items.return_value = item_urls

            mock_client = MagicMock()
            mock_aio = MagicMock()
            mock_models = MagicMock()
            mock_models.generate_content = AsyncMock(return_value=mock_response)
            mock_aio.models = mock_models
            mock_client.aio = mock_aio
            mock_genai.Client.return_value = mock_client

            from app.services.virtual_tryon import generate_tryon_image
            result = await generate_tryon_image(
                db=db_session,
                outfit_id=TEST_OUTFIT_ID,
                user_id=uuid.UUID(TEST_USER_ID),
            )

        assert result["outfit_id"] == TEST_OUTFIT_ID
        assert "/static/tryon/" in result["image_url"]
        assert result["image_url"].endswith(".png")
        assert result["cached"] is False

    @pytest.mark.asyncio
    async def test_generate_with_closet_item(self, db_session, seed_data):
        """옷장 아이템 포함 착장 생성."""
        mock_response = _mock_gemini_response()
        item_urls = ["https://example.com/shirt.jpg", "https://example.com/pants.jpg"]

        with (
            patch("app.services.virtual_tryon._fetch_image_bytes", new_callable=AsyncMock) as mock_fetch,
            patch("app.services.virtual_tryon._get_item_image_urls", new_callable=AsyncMock) as mock_items,
            patch("app.services.virtual_tryon.genai") as mock_genai,
        ):
            mock_fetch.return_value = FAKE_IMAGE_BYTES
            mock_items.return_value = item_urls

            mock_client = MagicMock()
            mock_aio = MagicMock()
            mock_models = MagicMock()
            mock_models.generate_content = AsyncMock(return_value=mock_response)
            mock_aio.models = mock_models
            mock_client.aio = mock_aio
            mock_genai.Client.return_value = mock_client

            from app.services.virtual_tryon import generate_tryon_image
            result = await generate_tryon_image(
                db=db_session,
                outfit_id=TEST_OUTFIT_ID,
                user_id=uuid.UUID(TEST_USER_ID),
                closet_item_id=uuid.UUID(TEST_CLOSET_ITEM_ID),
            )

        assert result["cached"] is False
        assert "/static/tryon/" in result["image_url"]
        assert result["image_url"].endswith(".png")

    @pytest.mark.asyncio
    async def test_cache_hit(self, db_session, seed_data):
        """캐시된 이미지가 있으면 API 호출 없이 반환."""
        cached_url = "data:image/png;base64,CACHED_IMAGE"

        with patch("app.services.virtual_tryon._check_cache", new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = cached_url

            from app.services.virtual_tryon import generate_tryon_image
            result = await generate_tryon_image(
                db=db_session,
                outfit_id=TEST_OUTFIT_ID,
                user_id=uuid.UUID(TEST_USER_ID),
            )

        assert result["cached"] is True
        assert result["image_url"] == cached_url

    @pytest.mark.asyncio
    async def test_outfit_not_found(self, db_session, seed_data):
        """존재하지 않는 코디 ID → ValueError."""
        from app.services.virtual_tryon import generate_tryon_image
        with pytest.raises(ValueError, match="코디를 찾을 수 없습니다"):
            await generate_tryon_image(
                db=db_session,
                outfit_id="nonexistent",
                user_id=uuid.UUID(TEST_USER_ID),
            )

    @pytest.mark.asyncio
    async def test_gemini_empty_response(self, db_session, seed_data):
        """Gemini가 이미지를 생성하지 못한 경우 → RuntimeError."""
        mock_response = _mock_gemini_empty_response()
        item_urls = ["https://example.com/shirt.jpg"]

        with (
            patch("app.services.virtual_tryon._fetch_image_bytes", new_callable=AsyncMock) as mock_fetch,
            patch("app.services.virtual_tryon._get_item_image_urls", new_callable=AsyncMock) as mock_items,
            patch("app.services.virtual_tryon.genai") as mock_genai,
        ):
            mock_fetch.return_value = FAKE_IMAGE_BYTES
            mock_items.return_value = item_urls

            mock_client = MagicMock()
            mock_aio = MagicMock()
            mock_models = MagicMock()
            mock_models.generate_content = AsyncMock(return_value=mock_response)
            mock_aio.models = mock_models
            mock_client.aio = mock_aio
            mock_genai.Client.return_value = mock_client

            from app.services.virtual_tryon import generate_tryon_image
            with pytest.raises(RuntimeError, match="이미지를 생성하지 못했습니다"):
                await generate_tryon_image(
                    db=db_session,
                    outfit_id=TEST_OUTFIT_ID,
                    user_id=uuid.UUID(TEST_USER_ID),
                )


class TestExtractImage:
    """_extract_image_from_response 유틸 테스트."""

    def test_extract_valid_image(self):
        from app.services.virtual_tryon import _extract_image_from_response
        response = _mock_gemini_response()
        result = _extract_image_from_response(response)
        assert result == FAKE_IMAGE_BYTES

    def test_extract_empty_candidates(self):
        from app.services.virtual_tryon import _extract_image_from_response
        response = _mock_gemini_empty_response()
        result = _extract_image_from_response(response)
        assert result is None


class TestImageToDataUrl:
    """_image_to_data_url 유틸 테스트."""

    def test_converts_to_data_url(self):
        from app.services.virtual_tryon import _image_to_data_url
        result = _image_to_data_url(b"test")
        assert result.startswith("data:image/png;base64,")
        assert "dGVzdA==" in result


class TestValidateImageUrl:
    """SSRF 방어 URL 검증 테스트."""

    def test_valid_https_url(self):
        from app.services.virtual_tryon import _validate_image_url
        _validate_image_url("https://example.com/image.jpg")

    def test_reject_localhost(self):
        from app.services.virtual_tryon import _validate_image_url
        with pytest.raises(ValueError, match="내부 네트워크"):
            _validate_image_url("http://localhost/secret")

    def test_reject_127_0_0_1(self):
        from app.services.virtual_tryon import _validate_image_url
        with pytest.raises(ValueError, match="내부 네트워크"):
            _validate_image_url("http://127.0.0.1/secret")

    def test_reject_private_ip(self):
        from app.services.virtual_tryon import _validate_image_url
        with pytest.raises(ValueError, match="내부 네트워크"):
            _validate_image_url("http://192.168.1.1/secret")

    def test_reject_metadata_ip(self):
        from app.services.virtual_tryon import _validate_image_url
        with pytest.raises(ValueError, match="내부 네트워크"):
            _validate_image_url("http://169.254.169.254/latest/meta-data")

    def test_reject_ftp_protocol(self):
        from app.services.virtual_tryon import _validate_image_url
        with pytest.raises(ValueError, match="허용되지 않는 프로토콜"):
            _validate_image_url("ftp://example.com/file")
