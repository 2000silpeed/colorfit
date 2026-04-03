"""A vs B 비교 API — GET /api/compare

두 코디를 5축 기준으로 비교하여 결정적 차이 요인을 반환한다.
기획서 섹션 6.3, 14.3 구현.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.schemas.outfit import (
    AxisComparison,
    CompareResponse,
    DecisiveFactor,
    OutfitBrief,
    ScoresResponse,
)
from app.services.comparator import compare_outfits
from app.utils import ensure_dict, ensure_list

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["compare"])


def _build_scores_response(scores: dict) -> ScoresResponse | None:
    if not scores:
        return None
    return ScoresResponse(
        pcf=scores.get("pcf", 0) or scores.get("personal_color_fit", 0),
        of_=scores.get("of", 0) or scores.get("occasion_fit", 0),
        ch=scores.get("ch", 0) or scores.get("color_harmony", 0),
        pe=scores.get("pe", 0) or scores.get("price_efficiency", 0),
        sf=scores.get("sf", 0) or scores.get("style_fit", 0),
    )


async def _get_outfit_image(outfit: Outfit, db: AsyncSession) -> str | None:
    item_ids = ensure_list(outfit.item_ids)
    if not item_ids:
        return None
    stmt = select(Product.image_url).where(Product.id == item_ids[0])
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    return row


@router.get("/compare", response_model=CompareResponse)
async def compare(
    ids: str = Query(..., description="비교할 코디 ID 2개 (콤마 구분)"),
    tone_id: str | None = Query(None, description="사용자 톤 ID (이유 생성용)"),
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if len(id_list) != 2:
        raise HTTPException(status_code=400, detail="정확히 2개의 코디 ID를 콤마로 구분하여 입력하세요")

    id_a, id_b = id_list

    stmt = select(Outfit).where(Outfit.id.in_([id_a, id_b]))
    result = await db.execute(stmt)
    outfits = {o.id: o for o in result.scalars().all()}

    if id_a not in outfits:
        raise HTTPException(status_code=404, detail=f"코디 {id_a}를 찾을 수 없습니다")
    if id_b not in outfits:
        raise HTTPException(status_code=404, detail=f"코디 {id_b}를 찾을 수 없습니다")

    outfit_a = outfits[id_a]
    outfit_b = outfits[id_b]

    scores_a = ensure_dict(outfit_a.scores)
    scores_b = ensure_dict(outfit_b.scores)

    comparison = compare_outfits(
        scores_a, scores_b,
        tone_id=tone_id,
        tpo_a=outfit_a.designed_tpo,
        tpo_b=outfit_b.designed_tpo,
    )

    image_a = await _get_outfit_image(outfit_a, db)
    image_b = await _get_outfit_image(outfit_b, db)

    df = comparison["decisive_factor"]

    return CompareResponse(
        outfit_a=OutfitBrief(
            id=outfit_a.id,
            gender=outfit_a.gender,
            designed_tpo=outfit_a.designed_tpo,
            total_price=outfit_a.total_price,
            scores=_build_scores_response(scores_a),
            image_url=image_a,
        ),
        outfit_b=OutfitBrief(
            id=outfit_b.id,
            gender=outfit_b.gender,
            designed_tpo=outfit_b.designed_tpo,
            total_price=outfit_b.total_price,
            scores=_build_scores_response(scores_b),
            image_url=image_b,
        ),
        axis_comparison=[
            AxisComparison(**ac) for ac in comparison["axis_comparison"]
        ],
        total_a=comparison["total_a"],
        total_b=comparison["total_b"],
        winner=comparison["winner"],
        decisive_factor=DecisiveFactor(**df),
    )
