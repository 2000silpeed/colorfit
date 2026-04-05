"""내 옷장 분석 + 역방향 추천 + 옷장 목록 API.

옷 사진 업로드 → 퍼스널컬러 점수 + 이유.
보유 옷 기반 → TPO별 어울리는 아이템 추천.
옷장 전체 아이템 목록 + 퍼스널컬러 적합도 통계.
기획서 섹션 5.5.1, F-39 구현.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.closet_item import ClosetItem
from app.schemas.closet import (
    ClosetAnalyzeRequest,
    ClosetAnalyzeResponse,
    ClosetItemAddRequest,
    ClosetItemAddResponse,
    ClosetItemResponse,
    ClosetListResponse,
    ClosetStats,
)
from app.schemas.closet_recommendation import (
    ClosetRecommendationResponse,
    RecommendedProduct,
    TpoOutfitSuggestion,
)
from app.services.closet_analyzer import analyze_closet_item
from app.services.closet_recommender import recommend_for_closet_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/closet", tags=["closet"])


@router.get("", response_model=ClosetListResponse)
async def get_closet(
    user_id: Annotated[uuid.UUID, Query()],
    db: AsyncSession = Depends(get_db),
) -> ClosetListResponse:
    """사용자 옷장 목록 + 퍼스널컬러 적합도 통계."""
    stmt = (
        select(ClosetItem)
        .where(ClosetItem.user_id == user_id)
        .order_by(ClosetItem.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    items = [
        ClosetItemResponse(
            id=str(row.id),
            image_url=row.image_url,
            category=row.category,
            dominant_color_hex=row.dominant_color_hex,
            matched_tone_id=row.matched_tone_id,
            pcf_score=row.pcf_score,
            overall_score=row.overall_score,
            reasons=row.reasons,
            created_at=str(row.created_at) if row.created_at else None,
        )
        for row in rows
    ]

    total_count = len(items)
    pcf_scores = [i.pcf_score for i in items if i.pcf_score is not None]
    average_pcf = sum(pcf_scores) / len(pcf_scores) if pcf_scores else 0.0
    good_count = sum(1 for s in pcf_scores if s >= 70)
    good_ratio = (good_count / total_count * 100) if total_count > 0 else 0.0

    stats = ClosetStats(
        total_count=total_count,
        average_pcf=round(average_pcf, 1),
        good_count=good_count,
        good_ratio=round(good_ratio, 1),
    )

    return ClosetListResponse(items=items, stats=stats)


@router.post("", response_model=ClosetItemAddResponse, status_code=201)
async def add_closet_item(
    req: ClosetItemAddRequest,
    db: AsyncSession = Depends(get_db),
) -> ClosetItemAddResponse:
    """사용자 옷장에 아이템 추가."""
    try:
        user_uuid = uuid.UUID(req.user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="유효하지 않은 user_id 형식입니다")

    item = ClosetItem(
        id=uuid.uuid4(),
        user_id=user_uuid,
        image_url=str(req.image_url),
        category=req.category,
        dominant_color_hex=req.dominant_color_hex,
        matched_tone_id=req.matched_tone_id,
        pcf_score=req.pcf_score,
        overall_score=req.overall_score,
        reasons=req.reasons,
    )
    db.add(item)
    try:
        await db.commit()
    except Exception:
        logger.exception("옷장 아이템 추가 실패")
        await db.rollback()
        raise HTTPException(status_code=500, detail="옷장 추가 중 오류가 발생했습니다")

    return ClosetItemAddResponse(id=str(item.id), message="옷장에 추가되었습니다")


@router.post("/analyze", response_model=ClosetAnalyzeResponse)
async def analyze_item(
    req: ClosetAnalyzeRequest,
) -> ClosetAnalyzeResponse:
    try:
        result = await analyze_closet_item(
            image_url=str(req.image_url),
            user_tone_id=req.user_tone_id,
        )
    except Exception:
        logger.exception("옷 분석 실패")
        raise HTTPException(status_code=500, detail="분석 중 오류가 발생했습니다")

    return ClosetAnalyzeResponse(**result)


@router.get("/recommendations", response_model=ClosetRecommendationResponse)
async def get_recommendations(
    color_hex: Annotated[str, Query(min_length=4, max_length=7)],
    category: str,
    user_tone_id: str,
    tpo: Annotated[str | None, Query()] = None,
    limit: int = Query(default=4, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> ClosetRecommendationResponse:
    """보유 옷 기반 역방향 추천.

    사용자 옷의 색상/카테고리에 맞는 아이템을 TPO별로 추천한다.
    """
    if not color_hex.startswith("#"):
        color_hex = f"#{color_hex}"

    tpo_list = [t.strip() for t in tpo.split(",")] if tpo else None

    try:
        results = await recommend_for_closet_item(
            db=db,
            source_color_hex=color_hex,
            source_category=category,
            user_tone_id=user_tone_id,
            tpo_list=tpo_list,
            limit_per_tpo=limit,
        )
    except Exception:
        logger.exception("역방향 추천 실패")
        raise HTTPException(status_code=500, detail="추천 중 오류가 발생했습니다")

    suggestions = [
        TpoOutfitSuggestion(
            tpo=r["tpo"],
            tpo_label=r["tpo_label"],
            items=[RecommendedProduct(**item) for item in r["items"]],
        )
        for r in results
    ]

    total = sum(len(s.items) for s in suggestions)

    return ClosetRecommendationResponse(
        source_color_hex=color_hex,
        source_category=category,
        user_tone_id=user_tone_id,
        recommendations=suggestions,
        total_count=total,
    )
