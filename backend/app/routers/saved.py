"""저장 목록 API — GET /api/saved

사용자가 저장한 코디 목록을 반환한다.
기획서 섹션 14.3 구현.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.schemas.outfit import OutfitFeedItem, ScoresResponse
from app.services.feed_builder import calculate_soft_score
from app.utils import ensure_dict, ensure_list

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["saved"])


class SavedResponse:
    pass


@router.get("/saved")
async def get_saved(
    user_id: str = Query(..., description="사용자 ID"),
    sort_by: str = Query("recent", description="정렬 기준 (recent/score/price)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # 1. 저장된 reaction 조회 (outfit_id만 선택하여 UUID 파싱 회피)
    stmt = select(Reaction.outfit_id).where(
        cast(Reaction.user_id, String) == user_id,
        Reaction.reaction_type == "save",
    ).order_by(Reaction.created_at.desc())

    result = await db.execute(stmt)
    raw_ids = result.scalars().all()

    outfit_ids = [oid for oid in raw_ids if oid]
    if not outfit_ids:
        return {"outfits": [], "total": 0}

    # reaction 순서 보존 (최근 저장 순)
    reaction_order = {oid: i for i, oid in enumerate(outfit_ids)}

    # 2. outfit 조회
    outfit_stmt = select(Outfit).where(Outfit.id.in_(outfit_ids))
    outfit_result = await db.execute(outfit_stmt)
    outfits_by_id = {o.id: o for o in outfit_result.scalars().all()}

    # 3. 아이템 이미지 일괄 로드
    all_item_ids: set[str] = set()
    outfit_first_item: dict[str, str] = {}
    for oid in outfit_ids:
        o = outfits_by_id.get(oid)
        if o:
            ids = ensure_list(o.item_ids)
            if ids:
                outfit_first_item[oid] = ids[0]
                all_item_ids.add(ids[0])

    image_map: dict[str, str | None] = {}
    if all_item_ids:
        prod_stmt = select(Product.id, Product.image_url).where(
            Product.id.in_(list(all_item_ids))
        )
        prod_result = await db.execute(prod_stmt)
        for pid, img in prod_result.all():
            image_map[pid] = img

    # 4. 응답 조립
    items: list[dict] = []
    for oid in outfit_ids:
        o = outfits_by_id.get(oid)
        if not o:
            continue

        scores = ensure_dict(o.scores)
        soft_score = calculate_soft_score(scores)
        first_item_id = outfit_first_item.get(oid)
        image_url = image_map.get(first_item_id) if first_item_id else None

        scores_resp = None
        if scores:
            scores_resp = {
                "pcf": scores.get("pcf", 0),
                "of": scores.get("of", 0),
                "ch": scores.get("ch", 0),
                "pe": scores.get("pe", 0),
                "sf": scores.get("sf", 0),
            }

        items.append({
            "id": o.id,
            "gender": o.gender,
            "designed_tpo": o.designed_tpo,
            "total_price": o.total_price,
            "tags": ensure_list(o.tags),
            "scores": scores_resp,
            "soft_score": soft_score,
            "reasons": ensure_list(o.reasons),
            "image_url": image_url,
            "reaction_order": reaction_order.get(oid, 0),
        })

    # 5. 정렬
    if sort_by == "score":
        items.sort(key=lambda x: x["soft_score"], reverse=True)
    elif sort_by == "price":
        items.sort(key=lambda x: x.get("total_price") if x.get("total_price") is not None else float("inf"))
    else:  # recent
        items.sort(key=lambda x: x["reaction_order"])

    # reaction_order 제거
    for item in items:
        item.pop("reaction_order", None)

    return {"outfits": items, "total": len(items)}
