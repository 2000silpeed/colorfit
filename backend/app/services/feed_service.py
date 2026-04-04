"""Feed Service — 코디 피드 비즈니스 로직.

라우터(feed.py)에서 분리된 비즈니스 로직:
- DB 쿼리 (필터 푸시다운 + 안전 LIMIT)
- 아이템 배치 로드
- Hard Filter + Soft Score + Rerank
- 응답 조립
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.schemas.outfit import (
    FeedResponse,
    FeedItemBrief,
    OutfitFeedItem,
    ScoresResponse,
)
from app.services.feed_builder import (
    apply_hard_filters,
    calculate_soft_score,
    rerank,
    _load_brand_whitelist,
    MONTH_TO_SEASON,
    OPPOSITE_SEASONS,
)
from app.services.reason_generator import generate_reasons
from app.services.scoring import TPO_SYNONYMS, calculate_of
from app.utils import ensure_list, ensure_dict

PAGE_SIZE = 20
MAX_OUTFIT_LOAD = 2000
PRODUCT_BATCH_SIZE = 500

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


def category_to_group(category: str | None) -> str:
    if not category:
        return ""
    return _GROUP_MAP.get(category, "")


def _build_item_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "brand": p.brand,
        "tone_id": p.tone_id,
        "category": p.category,
        "silhouette": p.silhouette,
        "group": category_to_group(p.category),
        "color_hex": p.color_hex,
        "price": p.price,
        "image_url": p.image_url,
        "style_tag": p.style_tag,
    }


def compute_outfit_metadata(
    items: list[dict],
    user_preferred: set[str] | None,
) -> dict:
    """아이템 리스트에서 dominant_tone, main_item_id, brand 비율 등을 계산."""
    whitelist = _load_brand_whitelist()
    tone_counts: dict[str, int] = {}
    main_item_id: str | None = None
    verified_count = 0
    preferred_count = 0

    for item in items:
        t = item.get("tone_id")
        if t:
            tone_counts[t] = tone_counts.get(t, 0) + 1
        if item.get("group") in ("top", "onepiece") and main_item_id is None:
            main_item_id = item["id"]
        brand_lower = item["brand"].lower() if item.get("brand") else ""
        if brand_lower and brand_lower in whitelist:
            verified_count += 1
        if user_preferred and brand_lower and brand_lower in user_preferred:
            preferred_count += 1

    dominant_tone = max(tone_counts, key=tone_counts.get) if tone_counts else None
    branded_count = sum(1 for it in items if it.get("brand"))
    verified_brand_ratio = verified_count / branded_count if branded_count else 0.0

    if user_preferred:
        bq_ratio = preferred_count / branded_count if branded_count else 0.0
    else:
        bq_ratio = verified_brand_ratio

    return {
        "dominant_tone": dominant_tone,
        "main_item_id": main_item_id,
        "verified_count": verified_count,
        "verified_brand_ratio": bq_ratio,
    }


async def _build_db_query(
    gender: str | None,
    age_group: str | None,
    tpo: str | None,
    budget_min: int | None,
    budget_max: int | None,
):
    """DB 레벨에서 가능한 필터를 WHERE로 푸시다운."""
    stmt = select(Outfit)

    if gender:
        stmt = stmt.where(
            (Outfit.gender == gender) | (Outfit.gender == "unisex") | (Outfit.gender.is_(None))
        )
    if age_group:
        stmt = stmt.where(
            (Outfit.age_group == age_group) | (Outfit.age_group.is_(None))
        )
    if tpo:
        tpo_expanded = list(TPO_SYNONYMS.get(tpo, {tpo}))
        stmt = stmt.where(
            Outfit.designed_tpo.in_(tpo_expanded) | Outfit.designed_tpo.is_(None)
        )
    if budget_min and budget_min > 0:
        stmt = stmt.where(
            (Outfit.total_price >= budget_min) | (Outfit.total_price.is_(None))
        )
    if budget_max and budget_max > 0:
        stmt = stmt.where(
            (Outfit.total_price <= budget_max) | (Outfit.total_price.is_(None))
        )

    # 반대 시즌 제외 (H3 DB 푸시다운, travel TPO는 시즌 무관이므로 제외하지 않음)
    current_month = datetime.now().month
    current_season = MONTH_TO_SEASON.get(current_month)
    if current_season:
        opposite = OPPOSITE_SEASONS.get(current_season)
        if opposite:
            stmt = stmt.where(
                (Outfit.designed_season != opposite)
                | (Outfit.designed_season.is_(None))
                | (Outfit.designed_tpo == "travel")
            )

    stmt = stmt.limit(MAX_OUTFIT_LOAD)
    return stmt


async def _load_items_batched(
    db: AsyncSession,
    outfits: list[Outfit],
) -> dict[str, list[dict]]:
    """outfit의 item_ids를 배치로 Product 조회하여 매핑."""
    outfit_item_ids_map: dict[str, list[str]] = {}
    all_item_ids: set[str] = set()

    for o in outfits:
        ids = ensure_list(o.item_ids)
        outfit_item_ids_map[o.id] = ids
        all_item_ids.update(ids)

    if not all_item_ids:
        return {}

    # 배치로 Product 조회 (IN 절 크기 제한)
    products_by_id: dict[str, Product] = {}
    id_list = list(all_item_ids)
    for i in range(0, len(id_list), PRODUCT_BATCH_SIZE):
        batch = id_list[i:i + PRODUCT_BATCH_SIZE]
        prod_result = await db.execute(
            select(Product).where(Product.id.in_(batch))
        )
        for p in prod_result.scalars().all():
            products_by_id[p.id] = p

    item_map: dict[str, list[dict]] = {}
    for outfit_id, ids in outfit_item_ids_map.items():
        items = []
        for pid in ids:
            p = products_by_id.get(pid)
            if p:
                items.append(_build_item_dict(p))
        item_map[outfit_id] = items

    return item_map


async def _load_disliked_ids(
    db: AsyncSession,
    user_id: str | None,
) -> set[str]:
    if not user_id:
        return set()
    result = await db.execute(
        select(Reaction.outfit_id).where(
            Reaction.reaction_type == "dislike",
            Reaction.user_id == user_id,
        )
    )
    return {r for r in result.scalars().all() if r}


def _score_outfit(
    o: Outfit,
    items: list[dict],
    user_profile: dict,
    tpo: str | None,
    user_preferred: set[str] | None,
    verified_only: bool,
) -> dict | None:
    """단일 outfit에 Hard Filter + Soft Score 적용. 탈락 시 None."""
    outfit_dict = {
        "gender": o.gender,
        "total_price": o.total_price,
        "designed_season": o.designed_season,
        "designed_tpo": o.designed_tpo,
        "llm_quality_score": o.llm_quality_score,
    }

    passed, _ = apply_hard_filters(outfit_dict, user_profile, items)
    if not passed:
        return None

    # OF 런타임 재계산
    scores_dict = ensure_dict(o.scores)
    user_tpo_for_of = [tpo] if tpo else (user_profile.get("tpo_list") or [])
    if user_tpo_for_of:
        runtime_of = calculate_of(ensure_list(o.tags), user_tpo_for_of)
        scores_dict = {**scores_dict, "of": runtime_of}

    soft_score = calculate_soft_score(scores_dict)
    _GROUP_PRIORITY = {"top": 0, "onepiece": 1, "outer": 2, "bottom": 3, "shoes": 4, "bag": 5, "acc": 6}
    sorted_items = sorted(items, key=lambda it: _GROUP_PRIORITY.get(it.get("group", ""), 99))
    image_url = sorted_items[0]["image_url"] if sorted_items else None

    meta = compute_outfit_metadata(items, user_preferred)

    if verified_only and (meta["verified_count"] == 0 or meta["verified_brand_ratio"] < 0.5):
        return None

    return {
        "id": o.id,
        "soft_score": soft_score,
        "runtime_scores": scores_dict,
        "is_complete_outfit": o.is_complete_outfit,
        "dominant_tone": meta["dominant_tone"],
        "main_item_id": meta["main_item_id"],
        "verified_brand_ratio": meta["verified_brand_ratio"],
        "outfit": o,
        "image_url": image_url,
    }


def _build_feed_item(
    entry: dict,
    item_map: dict[str, list[dict]],
    tone_id: str,
) -> OutfitFeedItem:
    """스코어링된 entry를 OutfitFeedItem으로 변환."""
    o: Outfit = entry["outfit"]
    scores = entry.get("runtime_scores") or ensure_dict(o.scores)

    precomputed_reasons = ensure_list(o.reasons)
    reasons = precomputed_reasons if precomputed_reasons else generate_reasons(
        scores,
        user_tone_id=tone_id,
        outfit_tpo=o.designed_tpo,
        outfit_id=o.id,
    )

    scores_resp = ScoresResponse(
        pcf=scores.get("pcf", 0) or scores.get("personal_color_fit", 0),
        of_=scores.get("of", 0) or scores.get("occasion_fit", 0),
        ch=scores.get("ch", 0) or scores.get("color_harmony", 0),
        pe=scores.get("pe", 0) or scores.get("price_efficiency", 0),
        sf=scores.get("sf", 0) or scores.get("style_fit", 0),
    ) if scores else None

    whitelist = _load_brand_whitelist()
    outfit_items = item_map.get(o.id, [])
    feed_item_briefs = [
        FeedItemBrief(
            image_url=it.get("image_url"),
            category=it.get("category"),
            group=it.get("group"),
            brand=it.get("brand"),
            style_tag=it.get("style_tag"),
            is_verified_brand=bool(it.get("brand") and it["brand"].lower() in whitelist),
        )
        for it in outfit_items
    ]

    return OutfitFeedItem(
        id=o.id,
        gender=o.gender,
        designed_tpo=o.designed_tpo,
        total_price=o.total_price,
        tags=ensure_list(o.tags),
        scores=scores_resp,
        soft_score=entry["soft_score"],
        final_score=entry.get("final_score", 0.0),
        reasons=reasons,
        image_url=entry.get("image_url"),
        items=feed_item_briefs,
    )


async def get_feed(
    db: AsyncSession,
    *,
    tone_id: str,
    gender: str | None = None,
    age_group: str | None = None,
    tpo: str | None = None,
    budget_min: int | None = None,
    budget_max: int | None = None,
    user_id: str | None = None,
    verified_only: bool = False,
    preferred_brands: str | None = None,
    page: int = 1,
) -> FeedResponse:
    """코디 피드 메인 파이프라인."""
    user_profile = {
        "gender": gender,
        "tone_id": tone_id,
        "tpo_list": [tpo] if tpo else [],
        "budget_min": budget_min,
        "budget_max": budget_max,
    }

    user_preferred: set[str] | None = None
    if preferred_brands:
        user_preferred = {b.strip().lower() for b in preferred_brands.split(",") if b.strip()}

    # 1. DB 쿼리 (필터 푸시다운 + LIMIT)
    stmt = await _build_db_query(gender, age_group, tpo, budget_min, budget_max)
    result = await db.execute(stmt)
    outfits = result.scalars().all()

    # 2. 아이템 배치 로드
    item_map = await _load_items_batched(db, outfits)

    # 3. dislike 로드
    disliked_ids = await _load_disliked_ids(db, user_id)

    # 4. Hard Filter + Soft Score
    scored: list[dict] = []
    for o in outfits:
        items = item_map.get(o.id, [])
        entry = _score_outfit(o, items, user_profile, tpo, user_preferred, verified_only)
        if entry:
            scored.append(entry)

    # 5. Rerank
    reranked = rerank(scored, disliked_ids=disliked_ids)
    total = len(reranked)

    # 6. 페이지네이션
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = reranked[start:end]

    # 7. 응답 조립
    feed_items = [_build_feed_item(entry, item_map, tone_id) for entry in page_items]

    return FeedResponse(
        outfits=feed_items,
        page=page,
        page_size=PAGE_SIZE,
        total=total,
        has_next=end < total,
    )
