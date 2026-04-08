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
from app.models.user import User

logger = logging.getLogger(__name__)

TRYON_MODEL = "gemini-2.5-flash-image"

# 퍼스널컬러 톤별 피부톤 + 조명 가이드 (nanobanana 테크닉 적용)
TONE_PROFILE: dict[str, dict[str, str]] = {
    "spring_warm_light": {
        "skin": "warm ivory skin with peachy-pink undertone, bright and clear complexion",
        "lighting": "5200K natural daylight with soft warm fill, enhancing peachy glow",
        "season": "spring",
    },
    "spring_warm_vivid": {
        "skin": "warm beige skin with golden undertone, vibrant and healthy glow",
        "lighting": "5000K golden hour warmth, slight amber rim light for radiance",
        "season": "spring",
    },
    "spring_warm_mute": {
        "skin": "warm ivory-beige skin with soft golden undertone, gentle warm glow",
        "lighting": "5500K soft diffused daylight, low contrast for muted harmony",
        "season": "spring",
    },
    "summer_cool_light": {
        "skin": "fair pinkish skin with cool rosy undertone, delicate and translucent",
        "lighting": "6500K cool daylight, soft overcast quality preserving pink undertone",
        "season": "summer",
    },
    "summer_cool_mute": {
        "skin": "light beige skin with soft lavender-pink undertone, muted and elegant",
        "lighting": "6000K diffused cloudy light, minimal shadows for soft muted effect",
        "season": "summer",
    },
    "summer_cool_soft": {
        "skin": "fair skin with subtle cool pink undertone, soft and refined complexion",
        "lighting": "6200K gentle overcast, soft fill light preserving cool undertone",
        "season": "summer",
    },
    "autumn_warm_mute": {
        "skin": "medium warm beige skin with olive-gold undertone, earthy and natural",
        "lighting": "4500K warm tungsten fill with natural window light, earthy warmth",
        "season": "autumn",
    },
    "autumn_warm_deep": {
        "skin": "medium-tan skin with rich golden-bronze undertone, deep warm glow",
        "lighting": "4000K warm golden light, slight amber tint accentuating bronze depth",
        "season": "autumn",
    },
    "autumn_warm_strong": {
        "skin": "warm honey-tan skin with strong golden undertone, rich and vibrant",
        "lighting": "4200K rich warm light with amber highlights, strong golden radiance",
        "season": "autumn",
    },
    "winter_cool_vivid": {
        "skin": "clear porcelain skin with blue-cool undertone, high contrast features",
        "lighting": "7000K crisp cool daylight, high contrast ratio for vivid clarity",
        "season": "winter",
    },
    "winter_cool_deep": {
        "skin": "medium skin with cool blue-brown undertone, deep and striking",
        "lighting": "6500K neutral-cool studio light, controlled shadows for depth",
        "season": "winter",
    },
    "winter_cool_strong": {
        "skin": "fair to medium skin with strong cool undertone, bold contrast",
        "lighting": "6800K cool studio key light, defined shadows for strong impact",
        "season": "winter",
    },
    "winter_cool_mute": {
        "skin": "cool beige skin with subtle blue undertone, smooth and refined",
        "lighting": "6200K soft cool light, even diffusion for refined muted quality",
        "season": "winter",
    },
}

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


def _make_profile_hash(
    tone_id: str | None, gender: str | None, age_group: str | None
) -> str:
    key = f"{tone_id or ''}:{gender or ''}:{age_group or ''}"
    return hashlib.md5(key.encode()).hexdigest()


async def _check_cache(
    db: AsyncSession,
    outfit_id: str,
    closet_item_id: uuid.UUID | None,
    user_id: uuid.UUID,
    profile_hash: str | None = None,
) -> str | None:
    stmt = select(TryonCache.image_url).where(
        TryonCache.outfit_id == outfit_id,
        TryonCache.user_id == user_id,
    )
    if closet_item_id:
        stmt = stmt.where(TryonCache.closet_item_id == closet_item_id)
    else:
        stmt = stmt.where(TryonCache.closet_item_id.is_(None))
    if profile_hash:
        stmt = stmt.where(TryonCache.profile_hash == profile_hash)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _save_cache(
    db: AsyncSession,
    outfit_id: str,
    closet_item_id: uuid.UUID | None,
    user_id: uuid.UUID,
    image_url: str,
    profile_hash: str | None = None,
) -> None:
    cache = TryonCache(
        outfit_id=outfit_id,
        closet_item_id=closet_item_id,
        user_id=user_id,
        image_url=image_url,
        profile_hash=profile_hash,
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
    # 사용자 톤 조회 (캐시 키에 필요하므로 먼저 조회)
    user_stmt = select(User.tone_id, User.gender, User.age_group).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user_row = user_result.first()
    user_tone_id = user_row.tone_id if user_row else None
    user_gender = user_row.gender if user_row else None
    user_age_group = user_row.age_group if user_row else None

    profile_hash = _make_profile_hash(user_tone_id, user_gender, user_age_group)

    cached_url = await _check_cache(db, outfit_id, closet_item_id, user_id, profile_hash)
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

    # 톤 프로필 조회
    tone_profile = TONE_PROFILE.get(user_tone_id or "", {})
    skin_desc = tone_profile.get("skin", "")
    lighting_desc = tone_profile.get("lighting", "5500K neutral daylight")
    gender_text = "female" if user_gender == "female" else "male" if user_gender == "male" else None
    age_text = {"20s": "early-to-mid 20s", "30s": "early-to-mid 30s", "40plus": "early 40s"}.get(
        user_age_group or "", None
    )

    # nanobanana 구조화 프롬프트: Subject → Wardrobe → Skin/Lighting → Camera → Style
    skin_block = ""
    if skin_desc:
        skin_block = (
            f"\n[SKIN TONE — CRITICAL]\n"
            f"Personal color type: {user_tone_id}\n"
            f"Skin: {skin_desc}\n"
            f"The model's face and body skin tone MUST precisely match this description. "
            f"This is essential — the image demonstrates outfit-skin harmony.\n"
        )

    lighting_block = (
        f"\n[LIGHTING]\n"
        f"Key light: {lighting_desc}\n"
        f"Soft diffused fill light from 45-degree angle, subtle rim light for depth separation. "
        f"No harsh shadows on face. Even illumination on garments to show true colors.\n"
    )

    camera_block = (
        "\n[CAMERA & COMPOSITION]\n"
        "Eye-level full-body shot at 1.6m height, 85mm equivalent focal length. "
        "Subject centered, 3:4 portrait aspect ratio. "
        "Shallow depth of field (f/2.8) with garments in sharp focus. "
        "Simple seamless light gray (#E8E8E8) studio backdrop.\n"
    )

    prompt_text = (
        f"[TASK] Generate a photorealistic fashion editorial full-body photo.\n"
        f"\n[SUBJECT]\n"
        f"East Asian{f' {gender_text}' if gender_text else ''} model"
        f"{f', {age_text} age range' if age_text else ''}, natural relaxed standing pose "
        f"with slight weight shift. Confident but approachable expression.\n"
        f"\n[WARDROBE — {len(item_infos)} ITEMS, ALL MUST BE WORN]\n"
        f"{items_text}\n"
        f"IMPORTANT: Every listed item must be clearly visible and correctly worn. "
        f"Preserve the exact color, fabric texture, and design details from each item image.\n"
        f"{skin_block}"
        f"{lighting_block}"
        f"{camera_block}"
        f"[STYLE]\n"
        f"High-end fashion magazine editorial (COS, SSENSE lookbook quality). "
        f"Clean, minimal, professional. No text overlays or watermarks."
    )

    if model_image_url:
        try:
            model_bytes = await _fetch_image_bytes(model_image_url)
            image_parts.append(
                types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg")
            )
            prompt_text = (
                f"[TASK] Generate a photorealistic fashion editorial full-body photo "
                f"using the reference model photo provided.\n"
                f"\n[SUBJECT]\n"
                f"Use the exact face and body proportions from the reference photo. "
                f"Natural relaxed standing pose with slight weight shift.\n"
                f"\n[WARDROBE — {len(item_infos)} ITEMS, ALL MUST BE WORN]\n"
                f"{items_text}\n"
                f"IMPORTANT: Every listed item must be clearly visible and correctly worn. "
                f"Preserve the exact color, fabric texture, and design details from each item image.\n"
                f"{skin_block}"
                f"{lighting_block}"
                f"{camera_block}"
                f"[STYLE]\n"
                f"High-end fashion magazine editorial (COS, SSENSE lookbook quality). "
                f"Clean, minimal, professional. No text overlays or watermarks."
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

    await _save_cache(db, outfit_id, closet_item_id, user_id, image_url, profile_hash)

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
