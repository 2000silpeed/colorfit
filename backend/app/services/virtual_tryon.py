"""Virtual Try-On 서비스.

Gemini 나노바나나(gemini-2.5-flash-image)로 코디 아이템 착장 이미지를 생성한다.
내 옷 이미지 + 추천 아이템 이미지 → 착장 합성 이미지.
기획서 F-41, F-54 구현.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import logging
import secrets
import uuid
from pathlib import Path
from urllib.parse import urlparse

import httpx
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.closet_item import ClosetItem
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.tryon_cache import TryonCache

logger = logging.getLogger(__name__)

TRYON_MODEL = "gemini-2.5-flash-image"

TRYON_STORAGE = Path(__file__).resolve().parents[2] / "storage" / "tryon"
TRYON_STORAGE.mkdir(parents=True, exist_ok=True)


DEFAULT_MODEL_IMAGES: dict[str, str] = {
    "male": "https://storage.googleapis.com/colorfit-assets/models/male_default.jpg",
    "female": "https://storage.googleapis.com/colorfit-assets/models/female_default.jpg",
}

ALLOWED_IMAGE_HOSTS: set[str] = {
    "storage.googleapis.com",
    "shopping-phinf.pstatic.net",
    "shop-phinf.pstatic.net",
    "example.com",
}


def _validate_image_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"허용되지 않는 프로토콜: {parsed.scheme}")
    hostname = parsed.hostname or ""
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", ""):
        raise ValueError("내부 네트워크 접근 불가")
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        raise ValueError("내부 네트워크 접근 불가")


async def _fetch_image_bytes(url: str) -> bytes:
    _validate_image_url(url)
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


class _ItemInfo:
    def __init__(self, image_url: str, name: str, category: str, color: str):
        self.image_url = image_url
        self.name = name
        self.category = category
        self.color = color


async def _get_item_infos(
    db: AsyncSession, outfit_id: str
) -> list[_ItemInfo]:
    stmt = select(Outfit).where(Outfit.id == outfit_id)
    result = await db.execute(stmt)
    outfit = result.scalar_one_or_none()
    if not outfit:
        raise ValueError(f"코디를 찾을 수 없습니다: {outfit_id}")

    if not outfit.item_ids:
        raise ValueError(f"코디에 아이템이 없습니다: {outfit_id}")

    stmt = select(Product).where(Product.id.in_(outfit.item_ids))
    result = await db.execute(stmt)
    products = result.scalars().all()
    return [
        _ItemInfo(
            image_url=p.image_url or "",
            name=p.name or "",
            category=p.category or "",
            color=p.color_hex or "",
        )
        for p in products
        if p.image_url
    ]


async def _check_cache(
    db: AsyncSession,
    outfit_id: str,
    closet_item_id: uuid.UUID | None,
    user_id: uuid.UUID,
) -> str | None:
    stmt = select(TryonCache.image_url).where(
        TryonCache.outfit_id == outfit_id,
        TryonCache.user_id == user_id,
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
    cached_url = await _check_cache(db, outfit_id, closet_item_id, user_id)
    if cached_url:
        return {"image_url": cached_url, "outfit_id": outfit_id, "cached": True}

    item_infos = await _get_item_infos(db, outfit_id)

    if closet_item_id:
        stmt = select(ClosetItem).where(ClosetItem.id == closet_item_id)
        result = await db.execute(stmt)
        closet_item = result.scalar_one_or_none()
        if closet_item and closet_item.image_url:
            item_infos.append(_ItemInfo(
                image_url=closet_item.image_url,
                name="내 옷",
                category=closet_item.category or "top",
                color=closet_item.dominant_color_hex or "",
            ))

    image_parts: list[types.Part] = []
    item_descriptions: list[str] = []
    for i, info in enumerate(item_infos, 1):
        img_bytes = await _fetch_image_bytes(info.image_url)
        image_parts.append(
            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        )
        desc = f"아이템 {i}: {info.category}"
        if info.color:
            desc += f" ({info.color})"
        if info.name:
            desc += f" - {info.name}"
        item_descriptions.append(desc)

    items_text = "\n".join(item_descriptions)
    prompt_text = (
        f"다음 {len(item_infos)}개 패션 아이템으로 구성된 코디 착장 사진을 생성해주세요.\n\n"
        f"{items_text}\n\n"
        "모든 아이템을 빠짐없이 착용한 전신 사진을 생성해주세요. "
        "각 아이템의 색상, 소재, 디테일을 정확히 반영해야 합니다. "
        "20대 아시아인 모델, 자연스러운 포즈, 심플한 밝은 회색 배경, "
        "패션 매거진 에디토리얼 스타일, 고품질 실사."
    )

    if model_image_url:
        try:
            model_bytes = await _fetch_image_bytes(model_image_url)
            image_parts.append(
                types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg")
            )
            prompt_text = (
                f"다음 {len(item_infos)}개 패션 아이템으로 구성된 코디 착장 사진을 생성해주세요.\n\n"
                f"{items_text}\n\n"
                "위 모델 사진의 인물이 모든 아이템을 빠짐없이 착용한 전신 사진을 생성해주세요. "
                "각 아이템의 색상, 소재, 디테일을 정확히 반영해야 합니다. "
                "자연스러운 포즈, 심플한 밝은 회색 배경, "
                "패션 매거진 에디토리얼 스타일, 고품질 실사."
            )
        except Exception as exc:
            logger.warning("model image fetch failed (%s), falling back to prompt-only", exc)

    image_parts.append(types.Part.from_text(text=prompt_text))

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

    # storage/tryon/*.png 저장 후 상대 URL 캐싱
    digest = hashlib.sha256(generated_image).hexdigest()[:16]
    filename = f"{digest}_{secrets.token_hex(4)}.png"
    filepath = TRYON_STORAGE / filename
    filepath.write_bytes(generated_image)
    image_url = f"{settings.api_url.rstrip('/')}/static/tryon/{filename}" if getattr(settings, "api_url", "") else f"/static/tryon/{filename}"

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
