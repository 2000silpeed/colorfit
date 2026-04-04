"""Feed API — GET /api/feed

코디 피드 엔드포인트. 전체 파이프라인:
Profile Load → Hard Filter → StyleFilter → Soft Score → Rerank → Reason
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.utils import ensure_list, ensure_dict
from app.schemas.outfit import FeedResponse, FeedItemBrief, OutfitFeedItem, ScoresResponse
from app.services.feed_builder import apply_hard_filters, calculate_soft_score, rerank, _load_brand_whitelist
from app.services.reason_generator import generate_reasons

router = APIRouter(prefix="/api", tags=["feed"])

PAGE_SIZE = 20


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    tone_id: str = Query(..., description="사용자 퍼스널컬러 톤 ID"),
    gender: str | None = Query(None, description="성별 (male/female)"),
    age_group: str | None = Query(None, description="연령대 (20s/30s/40plus)"),
    tpo: str | None = Query(None, description="TPO 필터 (commute, casual 등)"),
    budget_min: int | None = Query(None, ge=0, description="최소 예산"),
    budget_max: int | None = Query(None, ge=0, description="최대 예산"),
    user_id: str | None = Query(None, description="사용자 ID (dislike 필터용)"),
    verified_only: bool = Query(False, description="화이트리스트 브랜드만 포함된 코디"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    user_profile = {
        "gender": gender,
        "tone_id": tone_id,
        "tpo_list": [tpo] if tpo else [],
        "budget_min": budget_min,
        "budget_max": budget_max,
    }

    # 1. DB에서 코디 로드 (인덱스 활용 pre-filter)
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
        from app.services.scoring import TPO_SYNONYMS
        tpo_expanded = list(TPO_SYNONYMS.get(tpo, {tpo}))
        stmt = stmt.where(
            Outfit.designed_tpo.in_(tpo_expanded) | Outfit.designed_tpo.is_(None)
        )

    result = await db.execute(stmt)
    outfits = result.scalars().all()

    # 2. 아이템 일괄 로드
    all_outfit_ids = [o.id for o in outfits]
    item_map: dict[str, list[dict]] = {}

    if all_outfit_ids:
        # outfit.item_ids로 product 조회
        all_item_ids: set[str] = set()
        outfit_item_ids_map: dict[str, list[str]] = {}
        for o in outfits:
            ids = ensure_list(o.item_ids)
            outfit_item_ids_map[o.id] = ids
            all_item_ids.update(ids)

        if all_item_ids:
            prod_stmt = select(Product).where(Product.id.in_(list(all_item_ids)))
            prod_result = await db.execute(prod_stmt)
            products_by_id = {p.id: p for p in prod_result.scalars().all()}

            for outfit_id, ids in outfit_item_ids_map.items():
                items = []
                for pid in ids:
                    p = products_by_id.get(pid)
                    if p:
                        items.append({
                            "id": p.id,
                            "brand": p.brand,
                            "tone_id": p.tone_id,
                            "category": p.category,
                            "silhouette": p.silhouette,
                            "group": _category_to_group(p.category),
                            "color_hex": p.color_hex,
                            "price": p.price,
                            "image_url": p.image_url,
                            "style_tag": p.style_tag,
                        })
                item_map[outfit_id] = items

    # 3. dislike 로드 (user_id가 있으면 해당 사용자만)
    disliked_ids: set[str] = set()
    if user_id:
        dislike_stmt = select(Reaction.outfit_id).where(
            Reaction.reaction_type == "dislike",
            Reaction.user_id == user_id,
        )
        dislike_result = await db.execute(dislike_stmt)
        disliked_ids = {r for r in dislike_result.scalars().all() if r}

    # 4. Hard Filter + Soft Score
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

        # OF를 사용자 TPO 기준으로 런타임 재계산
        from app.services.scoring import calculate_of
        scores_dict = ensure_dict(o.scores)
        user_tpo_for_of = [tpo] if tpo else (user_profile.get("tpo_list") or [])
        if user_tpo_for_of:
            runtime_of = calculate_of(ensure_list(o.tags), user_tpo_for_of)
            scores_dict = {**scores_dict, "of": runtime_of}

        soft_score = calculate_soft_score(scores_dict)

        # 대표 이미지: 첫 번째 아이템 이미지
        image_url = items[0]["image_url"] if items else None

        # dominant_tone: 아이템 중 가장 많은 tone_id
        tone_counts: dict[str, int] = {}
        main_item_id: str | None = None
        whitelist = _load_brand_whitelist()
        verified_count = 0
        for item in items:
            t = item.get("tone_id")
            if t:
                tone_counts[t] = tone_counts.get(t, 0) + 1
            if item.get("group") in ("top", "onepiece") and main_item_id is None:
                main_item_id = item["id"]
            if item.get("brand") and item["brand"].lower() in whitelist:
                verified_count += 1

        dominant_tone = max(tone_counts, key=tone_counts.get) if tone_counts else None
        verified_brand_ratio = verified_count / len(items) if items else 0.0

        if verified_only and verified_brand_ratio < 1.0:
            continue

        scored.append({
            "id": o.id,
            "soft_score": soft_score,
            "runtime_scores": scores_dict,
            "is_complete_outfit": o.is_complete_outfit,
            "dominant_tone": dominant_tone,
            "main_item_id": main_item_id,
            "verified_brand_ratio": verified_brand_ratio,
            "outfit": o,
            "image_url": image_url,
        })

    # 5. Rerank
    reranked = rerank(scored, disliked_ids=disliked_ids)
    total = len(reranked)

    # 6. 페이지네이션
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = reranked[start:end]

    # 7. Reason 생성 + 응답 조립
    feed_items: list[OutfitFeedItem] = []
    for entry in page_items:
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

        outfit_items = item_map.get(o.id, [])
        whitelist = _load_brand_whitelist()
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

        feed_items.append(OutfitFeedItem(
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
        ))

    return FeedResponse(
        outfits=feed_items,
        page=page,
        page_size=PAGE_SIZE,
        total=total,
        has_next=end < total,
    )


# 카테고리 → 대카테고리 그룹 매핑 (간이)
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
