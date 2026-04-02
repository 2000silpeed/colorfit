"""내 옷장 분석 API.

옷 사진 업로드 → 퍼스널컬러 점수 + 이유.
기획서 섹션 5.5.1, F-39 구현.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.closet import ClosetAnalyzeRequest, ClosetAnalyzeResponse
from app.services.closet_analyzer import analyze_closet_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/closet", tags=["closet"])


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
