"""Virtual Try-On 서비스.

Gemini 나노바나나(gemini-2.5-flash-image)로 코디 아이템 착장 이미지를 생성한다.
내 옷 이미지 + 추천 아이템 이미지 → 착장 합성 이미지.
기획서 F-41, F-54 구현.
"""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
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

SUPABASE_STORAGE_BUCKET = "Tryon-images"


async def _upload_to_supabase(filename: str, image_data: bytes) -> str | None:
    """Supabase Storage에 이미지를 업로드하고 공개 URL을 반환한다."""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.supabase_url}/storage/v1/object/{SUPABASE_STORAGE_BUCKET}/{filename}",
                headers={
                    "Authorization": f"Bearer {settings.supabase_anon_key}",
                    "apikey": settings.supabase_anon_key,
                    "Content-Type": "image/png",
                },
                content=image_data,
            )
            if resp.status_code in (200, 201):
                return f"{settings.supabase_url}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{filename}"
            logger.warning("Supabase Storage upload failed: %s %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Supabase Storage upload error: %s", exc)
    return None


# 성별 × 연령별 기본 모델 이미지 (전신, 신발 포함, 흰 배경)
# 로컬: /static/models/ 경로로 서빙됨 (storage/models/)
# _get_default_model_url()에서 settings.api_url을 붙여 절대 URL로 변환
_MODEL_IMAGE_KEYS: dict[str, str] = {
    "female_20s": "models/female_20s.png",
    "female_30s": "models/female_30s.png",
    "female_40plus": "models/female_40plus.png",
    "male_20s": "models/male_20s.png",
    "male_30s": "models/male_30s.png",
    "male_40plus": "models/male_40plus.png",
    "female": "models/female_30s.png",
    "male": "models/male_30s.png",
}


async def _get_default_model_bytes(gender: str | None, age_group: str | None) -> bytes | None:
    """기본 모델 이미지를 반환한다. 로컬 → Supabase Storage 순서로 시도."""
    g = gender or "female"
    key = f"{g}_{age_group}" if age_group else g
    path = _MODEL_IMAGE_KEYS.get(key) or _MODEL_IMAGE_KEYS.get(g)
    if not path:
        return None

    # 1. 로컬 파일 시도
    filepath = Path(__file__).resolve().parents[2] / "storage" / path
    if filepath.exists():
        return filepath.read_bytes()

    # 2. Supabase Storage에서 다운로드 (Render 재배포 시 로컬 파일 유실 대응)
    if settings.supabase_url:
        try:
            url = f"{settings.supabase_url}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{path}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning("model image download non-200: %s status=%s", path, resp.status_code)
                return None
            data = resp.content
            try:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_bytes(data)
            except Exception as cache_exc:
                logger.warning("model image cache write failed (continuing): %s", cache_exc)
            logger.info("model image downloaded from Supabase: %s (%d bytes)", path, len(data))
            return data
        except Exception as exc:
            logger.warning("model image download failed: %s", exc)

    return None

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
    def __init__(self, image_url: str, name: str, category: str, color: str, product_id: str = ""):
        self.image_url = image_url
        self.name = name
        self.category = category
        self.color = color
        self.product_id = product_id


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
            product_id=p.id,
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


def _build_color_override_block(
    item_infos: list[_ItemInfo],
    color_overrides: dict[str, str] | None,
) -> str:
    if not color_overrides:
        return ""
    lines: list[str] = []
    for info in item_infos:
        if info.product_id in color_overrides:
            selected = color_overrides[info.product_id]
            lines.append(
                f"- \"{info.name}\" (item image above): render this item in {selected} color, "
                f"NOT in the color shown in the product image."
            )
    if not lines:
        return ""
    return (
        "\n[COLOR OVERRIDE — CRITICAL]\n"
        "The user selected specific colors for some items. "
        "You MUST render these items in the selected color:\n"
        + "\n".join(lines) + "\n"
    )


async def generate_tryon_image(
    db: AsyncSession,
    outfit_id: str,
    user_id: uuid.UUID,
    closet_item_id: uuid.UUID | None = None,
    model_image_url: str | None = None,
    color_overrides: dict[str, str] | None = None,
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

    color_suffix = ""
    if color_overrides:
        color_suffix = ":" + json.dumps(color_overrides, sort_keys=True, ensure_ascii=False)
    profile_hash = _make_profile_hash(user_tone_id, user_gender, user_age_group)
    if color_suffix:
        profile_hash = hashlib.md5((profile_hash + color_suffix).encode()).hexdigest()

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

    # 아이템 이미지 + JSON 라벨을 번갈아 배치 (신발을 마지막에 배치하여 강조)
    SHOE_CATEGORIES = {"스니커즈", "로퍼", "힐", "부츠", "샌들", "슬리퍼", "구두", "운동화", "플랫"}
    shoe_items: list[tuple[int, _ItemInfo]] = []
    other_items: list[tuple[int, _ItemInfo]] = []
    for i, info in enumerate(item_infos, 1):
        if info.category in SHOE_CATEGORIES:
            shoe_items.append((i, info))
        else:
            other_items.append((i, info))
    ordered_items = other_items + shoe_items  # 신발을 마지막에 → Gemini가 더 잘 기억

    content_parts: list[types.Part] = []

    # 모델 이미지를 맨 앞에 배치 (제품 이미지의 서양인 모델 영향 차단)
    early_model_bytes = await _get_default_model_bytes(user_gender, user_age_group)
    if early_model_bytes:
        early_mime = "image/png" if early_model_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
        content_parts.append(types.Part.from_text(
            text="★★★ MAIN SUBJECT REFERENCE — KOREAN EAST ASIAN MODEL ★★★\n"
                 "The following image shows the EXACT person who must appear in the final output. "
                 "Use this person's face, ethnicity (Korean East Asian), skin tone, hair, body, and proportions. "
                 "ABSOLUTELY DO NOT change the ethnicity. "
                 "Do NOT generate African, Caucasian, Latina, Middle Eastern, or any other ethnicity — only Korean East Asian. "
                 "Do NOT substitute with any model from the product images that follow."
        ))
        content_parts.append(types.Part.from_bytes(data=early_model_bytes, mime_type=early_mime))

    items_json: list[dict] = []
    for idx, info in ordered_items:
        img_bytes = await _fetch_image_bytes(info.image_url)
        is_shoe = info.category in SHOE_CATEGORIES
        item_meta = {
            "item": idx,
            "category": info.category,
            "name": info.name or None,
            "color": info.color or None,
        }
        if is_shoe:
            item_meta["priority"] = "HIGH — this exact shoe design must appear on the model's feet"
        items_json.append(item_meta)
        content_parts.append(types.Part.from_text(text=json.dumps(item_meta, ensure_ascii=False)))
        content_parts.append(
            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        )

    items_text = json.dumps(items_json, ensure_ascii=False, indent=2)

    # 톤 프로필 조회
    tone_profile = TONE_PROFILE.get(user_tone_id or "", {})
    skin_desc = tone_profile.get("skin", "")
    lighting_desc = tone_profile.get("lighting", "5500K neutral daylight")
    gender_text = "female" if user_gender == "female" else "male" if user_gender == "male" else "female"
    age_text = {"20s": "early-to-mid 20s", "30s": "early-to-mid 30s", "40plus": "early 40s"}.get(
        user_age_group or "", None
    )

    # nanobanana 구조화 프롬프트: Subject → Wardrobe → Skin/Lighting → Camera → Style
    if skin_desc:
        skin_block = (
            f"\n[SKIN TONE — CRITICAL]\n"
            f"Personal color type: {user_tone_id}\n"
            f"Skin: {skin_desc}\n"
            f"The model's face and body skin tone MUST precisely match this description. "
            f"This is essential — the image demonstrates outfit-skin harmony.\n"
        )
    else:
        # tone_id 없는 사용자도 한국인 톤 기본 강제 (Gemini 인종 표류 방지)
        skin_block = (
            "\n[SKIN TONE — CRITICAL]\n"
            "Korean / East Asian skin tone: warm light beige, smooth and refined. "
            "The model's face and body skin tone MUST be Korean East Asian. "
            "NOT African, NOT Caucasian, NOT Latina, NOT Middle Eastern.\n"
        )

    lighting_block = (
        f"\n[LIGHTING]\n"
        f"Key light: {lighting_desc}\n"
        f"Soft diffused fill light from 45-degree angle, subtle rim light for depth separation. "
        f"No harsh shadows on face. Even illumination on garments to show true colors.\n"
    )

    camera_block = (
        "\n[CAMERA & COMPOSITION]\n"
        "Full-body shot from head to toe — SHOES AND FEET MUST BE FULLY VISIBLE. "
        "Eye-level at 1.6m height, 85mm equivalent focal length. "
        "Subject centered, 3:4 portrait aspect ratio. "
        "Leave 10% margin below the shoes so nothing is cropped. "
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
        f"Dress the model in ALL the items shown above. Each item image is labeled.\n"
        f"{items_text}\n"
        f"IMPORTANT: Every listed item must be clearly visible and correctly worn. "
        f"Preserve the exact color, fabric texture, and design details from each item image.\n"
        f"SHOES: Pay special attention to footwear. The shoe design, color, and style must EXACTLY match "
        f"the shoe product image provided. Do NOT substitute with generic shoes.\n"
        f"CRITICAL: If any item image contains a human model, IGNORE that model completely. "
        f"Only use the reference model photo provided below. Extract ONLY the clothing item from product images.\n"
        f"{_build_color_override_block(item_infos, color_overrides)}"
        f"{skin_block}"
        f"{lighting_block}"
        f"{camera_block}"
        f"[STYLE]\n"
        f"High-end fashion magazine editorial (COS, SSENSE lookbook quality). "
        f"Clean, minimal, professional. No text overlays or watermarks."
    )

    # 모델 이미지 (이미 맨 앞에 배치됨). 없으면 폴백 시도.
    model_bytes = early_model_bytes
    if not model_bytes and model_image_url:
        try:
            model_bytes = await _fetch_image_bytes(model_image_url)
            if model_bytes:
                fb_mime = "image/png" if model_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
                content_parts.append(types.Part.from_text(text="[REFERENCE MODEL PHOTO — use this person's face and body]"))
                content_parts.append(types.Part.from_bytes(data=model_bytes, mime_type=fb_mime))
        except Exception as exc:
            logger.warning("user model image fetch failed (%s)", exc)

    if model_bytes:
        logger.info("reference model image attached: %d bytes", len(model_bytes))
        prompt_text = (
            f"[TASK] Generate a photorealistic fashion editorial full-body photo "
            f"using the reference model photo provided above.\n"
            f"\n[SUBJECT]\n"
            f"Use the exact face and body proportions from the reference model photo. "
            f"Natural relaxed standing pose with slight weight shift. "
            f"Full body from head to toe — shoes and feet MUST be fully visible.\n"
            f"\n[WARDROBE — {len(item_infos)} ITEMS, ALL MUST BE WORN]\n"
            f"Dress the model in ALL the items shown above. Each item image is labeled.\n"
            f"{items_text}\n"
            f"IMPORTANT: Every listed item must be clearly visible and correctly worn. "
            f"Preserve the exact color, fabric texture, and design details from each item image.\n"
            f"SHOES: Pay special attention to footwear. The shoe design, color, and style must EXACTLY match "
            f"the shoe product image provided. Do NOT substitute with generic shoes.\n"
            f"CRITICAL: If any item image contains a human model, IGNORE that model completely. "
            f"Only use the reference model photo above. Extract ONLY the clothing item from product images.\n"
            f"{_build_color_override_block(item_infos, color_overrides)}"
            f"{skin_block}"
            f"{lighting_block}"
            f"{camera_block}"
            f"[STYLE]\n"
            f"High-end fashion magazine editorial (COS, SSENSE lookbook quality). "
            f"Clean, minimal, professional. No text overlays or watermarks."
        )

    content_parts.append(types.Part.from_text(text=prompt_text))

    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model=TRYON_MODEL,
        contents=content_parts,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    generated_image = _extract_image_from_response(response)
    if not generated_image:
        raise RuntimeError("Gemini API에서 이미지를 생성하지 못했습니다")

    # Supabase Storage에 업로드 (재배포 시 유실 방지)
    digest = hashlib.sha256(generated_image).hexdigest()[:16]
    filename = f"{digest}_{secrets.token_hex(4)}.png"
    image_url = await _upload_to_supabase(filename, generated_image)
    if not image_url:
        # fallback: 로컬 저장
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


COLOR_EXTRACT_MODEL = "gemini-2.5-flash"

COLOR_EXTRACT_PROMPT = (
    "이 패션 상품 이미지를 보고, 이 상품에서 선택 가능한 색상 옵션을 분석해줘.\n\n"
    "규칙:\n"
    "1. 이미지에 여러 색상의 동일 상품이 보이면, 각 색상을 리스트로 나열\n"
    "2. 단일 상품이지만 여러 색이 섞인 패턴이면, 주요 색상 2~3개를 나열\n"
    "3. 각 색상에 대해 한글 이름과 HEX 코드를 제공\n"
    "4. 최대 5개까지만\n\n"
    "JSON 배열로만 답해. 설명 없이.\n"
    '예: [{"name": "블랙", "hex": "#000000"}, {"name": "화이트", "hex": "#FFFFFF"}]'
)


async def extract_colors_from_product(image_url: str) -> list[dict[str, str]]:
    """상품 이미지에서 선택 가능한 색상 옵션을 Gemini로 추출한다."""
    img_bytes = await _fetch_image_bytes(image_url)
    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model=COLOR_EXTRACT_MODEL,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
            COLOR_EXTRACT_PROMPT,
        ],
    )

    text = (response.text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        text = text.rsplit("```", 1)[0]

    try:
        colors = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("색상 추출 JSON 파싱 실패: %s", text[:200])
        return []

    return [{"name": c["name"], "hex": c["hex"]} for c in colors[:5]]
