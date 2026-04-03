"""Top Pick API — GET /api/top-pick

최적 코디 1개를 선정하여 반환한다.
기획서 섹션 6.3, 14.3 구현.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.outfit import TopPickResponse, ScoresResponse, ProductBrief
from app.services.top_pick import get_top_pick

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["top-pick"])


@router.get("/top-pick", response_model=TopPickResponse)
async def top_pick(
    tone_id: str = Query(..., description="사용자 퍼스널컬러 톤 ID"),
    gender: str | None = Query(None, description="성별 (male/female)"),
    tpo: str | None = Query(None, description="TPO 필터"),
    budget_min: int | None = Query(None, ge=0, description="최소 예산"),
    budget_max: int | None = Query(None, ge=0, description="최대 예산"),
    user_id: str | None = Query(None, description="사용자 ID (저장 목록 기반 필터용)"),
    current_hour: int | None = Query(None, ge=0, le=23, description="시간대 (테스트용)"),
    db: AsyncSession = Depends(get_db),
) -> TopPickResponse:
    user_profile = {
        "gender": gender,
        "tone_id": tone_id,
        "tpo_list": [tpo] if tpo else [],
        "budget_min": budget_min,
        "budget_max": budget_max,
    }

    try:
        result = await get_top_pick(
            user_profile=user_profile,
            db=db,
            user_id=user_id,
            current_hour=current_hour,
        )
    except Exception:
        logger.exception("Top Pick 선정 실패")
        raise HTTPException(status_code=500, detail="Top Pick을 선정할 수 없습니다")

    if result is None:
        raise HTTPException(status_code=404, detail="조건에 맞는 코디가 없습니다")

    scores = result.get("scores")
    scores_resp = ScoresResponse(
        pcf=scores.get("pcf", 0) or scores.get("personal_color_fit", 0),
        of_=scores.get("of", 0) or scores.get("occasion_fit", 0),
        ch=scores.get("ch", 0) or scores.get("color_harmony", 0),
        pe=scores.get("pe", 0) or scores.get("price_efficiency", 0),
        sf=scores.get("sf", 0) or scores.get("style_fit", 0),
    ) if scores else None

    items = [
        ProductBrief(
            id=item["id"],
            name=item.get("name"),
            brand=item.get("brand"),
            category=item.get("category"),
            price=item.get("price"),
            image_url=item.get("image_url"),
            mall_url=item.get("mall_url"),
        )
        for item in result.get("items", [])
    ]

    return TopPickResponse(
        id=result["id"],
        gender=result.get("gender"),
        designed_tpo=result.get("designed_tpo"),
        total_price=result.get("total_price"),
        tags=result.get("tags"),
        scores=scores_resp,
        soft_score=result.get("soft_score", 0.0),
        final_score=result.get("final_score", 0.0),
        reasons=result.get("reasons", []),
        highlight_reason=result.get("highlight_reason", ""),
        source=result.get("source", "db"),
        image_url=result.get("image_url"),
        items=items,
    )
