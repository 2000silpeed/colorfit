"""Virtual Try-On 서비스.

Gemini 나노바나나(gemini-2.5-flash-image)로 코디 아이템 착장 이미지를 생성한다.
내 옷 이미지 + 추천 아이템 이미지 → 착장 합성 이미지.
기획서 F-41, F-54 구현.
"""

from __future__ import annotations

import base64
import logging
import uuid
from io import BytesIO

import httpx
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.closet_item import ClosetItem
from app.models.outfit import Outfit
from app.models.tryon_cache import TryonCache

logger = logging.getLogger(__name__)

TRYON_MODEL = "gemini-2.5-flash-preview-image-generation"

TRYON_PROMPT = (
    "이 사람이 위 패션 아이템들을 착용한 전신 패션 사진을 생성해주세요. "
    "자연스러운 포즈, 심플한 배경, 패션 매거진 에디토리얼 스타일. "
    "아이템의 색상과 디테일을 최대한 유지해주세요."
)

DEFAULT_MODEL_IMAGES: dict[str, str] = {
    "male": "https://storage.googleapis.com/colorfit-assets/models/male_default.jpg",
    "female": "https://storage.googleapis.com/colorfit-assets/models/female_default.jpg",
}


async def _fetch_image_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def _get_item_image_urls(
    db: AsyncSession, outfit_id: str
) -> list[str]:
    stmt = select(Outfit).where(Outfit.id == outfit_id)
    result = await db.execute(stmt)
    outfit = result.scalar_one_or_none()
    if not outfit:
        raise ValueError(f"코디를 찾을 수 없습니다: {outfit_id}")

    if not outfit.item_ids:
        raise ValueError(f"코디에 아이템이 없습니다: {outfit_id}")

    from app.models.product import Product

    stmt = select(Product.image_url).where(Product.id.in_(outfit.item_ids))
    result = await db.execute(stmt)
    urls = result.scalars().all()
    return [u for u in urls if u]


async def _check_cache(
    db: AsyncSession,
    outfit_id: str,
    closet_item_id: uuid.UUID | None,
) -> str | None:
    stmt = select(TryonCache.image_url).where(
        TryonCache.outfit_id == outfit_id,
    )
    if closet_item_id:
        stmt = stmt.where(TryonCache.closet_item_id == closet_item_id)
    else:
        stmt = stmt.where(TryonCache.closet_item_id.is_(None))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _save_cache(
    db: AsyncSession,
    outfit_id: str,
    closet_item_id: uuid.UUID | None,
    user_id: uuid.UUID,
    image_url: str,
) -> None:
    cache = TryonCache(
        outfit_id=outfit_id,
        closet_item_id=closet_item_id,
        user_id=user_id,
        image_url=image_url,
    )
    db.add(cache)
    await db.commit()


async def generate_tryon_image(
    db: AsyncSession,
    outfit_id: str,
    user_id: uuid.UUID,
    closet_item_id: uuid.UUID | None = None,
    model_image_url: str | None = None,
) -> dict:
    """착장 이미지를 생성한다.

    1. 캐시 확인 → 있으면 바로 반환
    2. 코디 아이템 이미지 + 모델 이미지 수집
    3. Gemini API로 합성 이미지 생성
    4. 결과 캐싱 후 반환
    """
    cached_url = await _check_cache(db, outfit_id, closet_item_id)
    if cached_url:
        return {"image_url": cached_url, "outfit_id": outfit_id, "cached": True}

    item_image_urls = await _get_item_image_urls(db, outfit_id)

    if closet_item_id:
        stmt = select(ClosetItem.image_url).where(ClosetItem.id == closet_item_id)
        result = await db.execute(stmt)
        closet_url = result.scalar_one_or_none()
        if closet_url:
            item_image_urls.append(closet_url)

    if not model_image_url:
        model_image_url = DEFAULT_MODEL_IMAGES.get("female")

    image_parts: list[types.Part] = []
    for url in item_image_urls:
        img_bytes = await _fetch_image_bytes(url)
        image_parts.append(
            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        )

    model_bytes = await _fetch_image_bytes(model_image_url)
    image_parts.append(
        types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg")
    )

    image_parts.append(types.Part.from_text(text=TRYON_PROMPT))

    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model=TRYON_MODEL,
        contents=image_parts,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    generated_image = _extract_image_from_response(response)
    if not generated_image:
        raise RuntimeError("Gemini API에서 이미지를 생성하지 못했습니다")

    image_url = _image_to_data_url(generated_image)

    await _save_cache(db, outfit_id, closet_item_id, user_id, image_url)

    return {"image_url": image_url, "outfit_id": outfit_id, "cached": False}


def _extract_image_from_response(response) -> bytes | None:
    if not response.candidates:
        return None
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            return part.inline_data.data
    return None


def _image_to_data_url(image_data: bytes) -> str:
    b64 = base64.b64encode(image_data).decode("utf-8")
    return f"data:image/png;base64,{b64}"
