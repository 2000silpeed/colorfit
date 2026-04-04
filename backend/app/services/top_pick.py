"""Top Pick 서비스 — 최적 코디 1개 선정.

기획서 섹션 6.3 구현.
우선순위: 저장 목록 기반 → 전체 DB 기반 (콜드스타트)
시간대 기반 TPO 자동 추론으로 OF 점수 반영.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.utils import ensure_dict, ensure_list
from app.services.feed_builder import apply_hard_filters, calculate_soft_score, rerank
from app.services.reason_generator import generate_reasons, _select_top_axes, _render_template, _load_tone_names


TIME_SLOT_TPOS: dict[str, list[str]] = {
    "morning": ["office", "interview", "daily"],
    "afternoon": ["casual", "travel", "daily"],
    "evening": ["date", "party", "daily"],
}


def _infer_time_slot(hour: int | None = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"


def _merge_tpo_list(
    user_tpo_list: list[str] | None,
    current_hour: int | None = None,
) -> list[str]:
    """사용자 TPO + 시간대 TPO를 합산한다."""
    slot = _infer_time_slot(current_hour)
    time_tpos = TIME_SLOT_TPOS.get(slot, [])
    user_tpos = user_tpo_list or []
    merged = list(dict.fromkeys(user_tpos + time_tpos))
    return merged


_GROUP_MAP: dict[str, str] = {
    "티셔츠": "top", "셔츠": "top", "블라우스": "top", "니트": "top",
    "맨투맨": "top", "후드": "top", "탱크톱": "top", "크롭탑": "top",
    "자켓": "outer", "코트": "outer", "패딩": "outer", "가디건": "outer",
    "점퍼": "outer", "블레이저": "outer", "야상": "outer", "바람막이": "outer",
    "청바지": "bottom", "슬랙스": "bottom", "면바지": "bottom", "반바지": "bottom",
    "스커트": "bottom", "와이드팬츠": "bottom", "레깅스": "bottom",
    "원피스": "onepiece", "점프수트": "onepiece",
    "스니커즈": "shoes", "로퍼": "shoes", "부츠": "shoes", "샌들": "shoes",
    "힐": "shoes", "플랫슈즈": "shoes", "슬리퍼": "shoes",
    "가방": "bag", "백팩": "bag", "토트백": "bag", "크로스백": "bag",
    "모자": "acc", "머플러": "acc", "벨트": "acc", "주얼리": "acc",
    "시계": "acc", "선글라스": "acc", "스카프": "acc",
}


def _category_to_group(category: str | None) -> str:
    if not category:
        return ""
    return _GROUP_MAP.get(category, "")


def _build_item_dicts(products: list[Any]) -> dict[str, list[dict]]:
    """Product 리스트를 outfit_id별 아이템 dict 리스트로 빌드하지 않고,
    product_id → dict 매핑을 반환한다."""
    return {
        p.id: {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "tone_id": p.tone_id,
            "category": p.category,
            "silhouette": p.silhouette,
            "group": _category_to_group(p.category),
            "color_hex": p.color_hex,
            "price": p.price,
            "image_url": p.image_url,
            "mall_url": p.mall_url,
        }
        for p in products
    }


def _generate_highlight_reason(
    scores: dict[str, float],
    user_tone_id: str | None = None,
    outfit_tpo: str | None = None,
) -> str:
    """최고 기여도 축 1개의 이유를 반환한다."""
    if not scores:
        return ""
    top = _select_top_axes(scores, n=1)
    if not top:
        return ""
    axis, raw_score, _ = top[0]
    tone_name = None
    if user_tone_id:
        tone_names = _load_tone_names()
        tone_name = tone_names.get(user_tone_id)
    seed = str(scores.get("pcf", 0))
    return _render_template(axis, raw_score, seed, tone_name, outfit_tpo)


async def _load_saved_outfit_ids(
    user_id: str,
    db: AsyncSession,
) -> list[str]:
    """사용자가 저장한 코디 ID 목록을 반환한다."""
    stmt = select(Reaction.outfit_id).where(
        cast(Reaction.user_id, String) == user_id,
        Reaction.reaction_type == "save",
    )
    result = await db.execute(stmt)
    return [r for r in result.scalars().all() if r]


async def _load_outfits_with_items(
    db: AsyncSession,
    outfit_ids: list[str] | None = None,
    gender: str | None = None,
    tpo: str | None = None,
) -> tuple[list[Any], dict[str, list[dict]]]:
    """코디와 아이템을 로드한다.

    Returns:
        (outfits, item_map): outfit 리스트와 outfit_id → 아이템 리스트 매핑
    """
    stmt = select(Outfit)
    if outfit_ids is not None:
        stmt = stmt.where(Outfit.id.in_(outfit_ids))
    else:
        if gender:
            stmt = stmt.where(
                (Outfit.gender == gender) | (Outfit.gender == "unisex") | (Outfit.gender.is_(None))
            )
        if tpo:
            stmt = stmt.where(
                (Outfit.designed_tpo == tpo) | (Outfit.designed_tpo.is_(None))
            )

    result = await db.execute(stmt)
    outfits = result.scalars().all()

    all_item_ids: set[str] = set()
    outfit_item_ids_map: dict[str, list[str]] = {}
    for o in outfits:
        ids = ensure_list(o.item_ids)
        outfit_item_ids_map[o.id] = ids
        all_item_ids.update(ids)

    item_map: dict[str, list[dict]] = {}
    if all_item_ids:
        prod_stmt = select(Product).where(Product.id.in_(list(all_item_ids)))
        prod_result = await db.execute(prod_stmt)
        products_by_id = _build_item_dicts(prod_result.scalars().all())

        for outfit_id, ids in outfit_item_ids_map.items():
            items = [products_by_id[pid] for pid in ids if pid in products_by_id]
            item_map[outfit_id] = items

    return outfits, item_map


def _apply_time_tpo_bonus(
    scores: dict[str, float],
    outfit_tpo: str | None,
    time_tpos: list[str],
) -> dict[str, float]:
    """시간대 TPO 매칭 시 OF 점수에 보너스를 적용한다.

    코디의 designed_tpo가 시간대 TPO에 매칭되면 OF +10 (최대 100).
    프리컴퓨팅 원칙 유지: 원본 scores를 복사 후 보정만 수행.
    """
    if not outfit_tpo or not time_tpos:
        return scores
    if outfit_tpo not in time_tpos:
        return scores
    adjusted = dict(scores)
    adjusted["of"] = min(100.0, adjusted.get("of", 0.0) + 10.0)
    return adjusted


def _score_and_filter(
    outfits: list[Any],
    item_map: dict[str, list[dict]],
    user_profile: dict[str, Any],
    time_tpos: list[str] | None = None,
) -> list[dict]:
    """Hard Filter + Soft Score를 적용하여 후보 리스트를 반환한다."""
    scored: list[dict] = []
    for o in outfits:
        outfit_dict = {
            "gender": o.gender,
            "total_price": o.total_price,
            "designed_season": o.designed_season,
            "designed_tpo": o.designed_tpo,
            "llm_quality_score": o.llm_quality_score,
        }
        items = item_map.get(o.id, [])

        passed, _ = apply_hard_filters(outfit_dict, user_profile, items)
        if not passed:
            continue

        scores = ensure_dict(o.scores)
        if time_tpos:
            scores = _apply_time_tpo_bonus(scores, o.designed_tpo, time_tpos)
        soft_score = calculate_soft_score(scores)
        image_url = items[0]["image_url"] if items else None

        tone_counts: dict[str, int] = {}
        main_item_id: str | None = None
        for item in items:
            t = item.get("tone_id")
            if t:
                tone_counts[t] = tone_counts.get(t, 0) + 1
            if item.get("group") in ("top", "onepiece") and main_item_id is None:
                main_item_id = item["id"]

        dominant_tone = max(tone_counts, key=tone_counts.get) if tone_counts else None

        scored.append({
            "id": o.id,
            "soft_score": soft_score,
            "is_complete_outfit": o.is_complete_outfit,
            "dominant_tone": dominant_tone,
            "main_item_id": main_item_id,
            "outfit": o,
            "image_url": image_url,
            "adjusted_scores": scores,
        })

    return scored


async def get_top_pick(
    user_profile: dict[str, Any],
    db: AsyncSession,
    user_id: str | None = None,
    current_hour: int | None = None,
) -> dict[str, Any] | None:
    """Top Pick 코디 1개를 선정한다.

    기획서 섹션 6.3 구현.

    Args:
        user_profile: {tone_id, gender, tpo_list, budget_min, budget_max}
        db: DB 세션
        user_id: 사용자 ID (저장 목록 기반 필터용)
        current_hour: 현재 시각 (테스트용, None이면 현재 시간)

    Returns:
        Top Pick 코디 dict 또는 None (후보 없음)
    """
    merged_tpo = _merge_tpo_list(user_profile.get("tpo_list"), current_hour)
    profile_with_tpo = {**user_profile, "tpo_list": merged_tpo}

    slot = _infer_time_slot(current_hour)
    time_tpos = TIME_SLOT_TPOS.get(slot, [])

    source = "db"
    top_entry: dict | None = None

    # 1차: 저장 목록 기반
    if user_id:
        saved_ids = await _load_saved_outfit_ids(user_id, db)
        if saved_ids:
            outfits, item_map = await _load_outfits_with_items(db, outfit_ids=saved_ids)
            scored = _score_and_filter(outfits, item_map, profile_with_tpo, time_tpos)
            if scored:
                reranked = rerank(scored, limit=1)
                if reranked:
                    top_entry = reranked[0]
                    source = "saved"

    # 2차: 전체 DB 기반 (콜드스타트)
    if top_entry is None:
        outfits, item_map = await _load_outfits_with_items(
            db,
            gender=user_profile.get("gender"),
        )
        scored = _score_and_filter(outfits, item_map, profile_with_tpo, time_tpos)
        if scored:
            reranked = rerank(scored, limit=1)
            if reranked:
                top_entry = reranked[0]
                source = "db"

    if top_entry is None:
        return None

    o: Any = top_entry["outfit"]
    scores = top_entry.get("adjusted_scores") or ensure_dict(o.scores)
    tone_id = user_profile.get("tone_id")

    precomputed_reasons = ensure_list(o.reasons)
    reasons = precomputed_reasons if precomputed_reasons else generate_reasons(
        scores,
        user_tone_id=tone_id,
        outfit_tpo=o.designed_tpo,
    )

    highlight = _generate_highlight_reason(scores, tone_id, o.designed_tpo)

    items = item_map.get(o.id, [])

    return {
        "id": o.id,
        "gender": o.gender,
        "designed_tpo": o.designed_tpo,
        "total_price": o.total_price,
        "tags": ensure_list(o.tags),
        "scores": scores,
        "soft_score": top_entry["soft_score"],
        "final_score": top_entry.get("final_score", 0.0),
        "reasons": reasons,
        "highlight_reason": highlight,
        "source": source,
        "image_url": top_entry.get("image_url"),
        "items": items,
    }
