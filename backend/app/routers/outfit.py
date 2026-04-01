"""Outfit API — GET /api/outfit/{id}

단일 코디 상세 조회 엔드포인트.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.schemas.outfit import OutfitDetailResponse, ProductBrief, ScoresResponse
from app.utils import ensure_list, ensure_dict

router = APIRouter(prefix="/api", tags=["outfit"])


@router.get("/outfit/{outfit_id}", response_model=OutfitDetailResponse)
async def get_outfit(
    outfit_id: str,
    db: AsyncSession = Depends(get_db),
) -> OutfitDetailResponse:
    result = await db.execute(select(Outfit).where(Outfit.id == outfit_id))
    outfit = result.scalar_one_or_none()

    if not outfit:
        raise HTTPException(status_code=404, detail="코디를 찾을 수 없습니다")

    item_ids = ensure_list(outfit.item_ids)

    items: list[ProductBrief] = []
    if item_ids:
        prod_result = await db.execute(
            select(Product).where(Product.id.in_(item_ids))
        )
        products = prod_result.scalars().all()
        id_order = {pid: i for i, pid in enumerate(item_ids)}
        products_sorted = sorted(products, key=lambda p: id_order.get(p.id, 999))

        items = [
            ProductBrief(
                id=p.id,
                name=p.name,
                brand=p.brand,
                category=p.category,
                price=p.price,
                image_url=p.image_url,
                mall_url=p.mall_url,
            )
            for p in products_sorted
        ]

    scores = ensure_dict(outfit.scores)
    scores_resp = ScoresResponse(
        pcf=scores.get("pcf", 0),
        of_=scores.get("of", 0),
        ch=scores.get("ch", 0),
        pe=scores.get("pe", 0),
        sf=scores.get("sf", 0),
    ) if scores else None

    return OutfitDetailResponse(
        id=outfit.id,
        gender=outfit.gender,
        designed_tpo=outfit.designed_tpo,
        designed_season=outfit.designed_season,
        designed_moods=ensure_list(outfit.designed_moods),
        total_price=outfit.total_price,
        lowest_total_price=outfit.lowest_total_price,
        is_complete_outfit=outfit.is_complete_outfit,
        tags=ensure_list(outfit.tags),
        scores=scores_resp,
        reasons=ensure_list(outfit.reasons),
        items=items,
    )
