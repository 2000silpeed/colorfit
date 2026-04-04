"""Feed API — GET /api/feed

코디 피드 엔드포인트. 비즈니스 로직은 services/feed_service.py에 위임.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.outfit import FeedResponse
from app.services.feed_service import get_feed

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/feed", response_model=FeedResponse)
async def feed_endpoint(
    tone_id: str = Query(..., description="사용자 퍼스널컬러 톤 ID"),
    gender: str | None = Query(None, description="성별 (male/female)"),
    age_group: str | None = Query(None, description="연령대 (20s/30s/40plus)"),
    tpo: str | None = Query(None, description="TPO 필터 (commute, casual 등)"),
    budget_min: int | None = Query(None, ge=0, description="최소 예산"),
    budget_max: int | None = Query(None, ge=0, description="최대 예산"),
    user_id: str | None = Query(None, description="사용자 ID (dislike 필터용)"),
    verified_only: bool = Query(False, description="화이트리스트 브랜드만 포함된 코디"),
    preferred_brands: str | None = Query(None, description="사용자 선호 브랜드 (콤마 구분)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    return await get_feed(
        db,
        tone_id=tone_id,
        gender=gender,
        age_group=age_group,
        tpo=tpo,
        budget_min=budget_min,
        budget_max=budget_max,
        user_id=user_id,
        verified_only=verified_only,
        preferred_brands=preferred_brands,
        page=page,
    )
