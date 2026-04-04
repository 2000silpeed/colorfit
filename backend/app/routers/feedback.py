"""Feedback API — 피드백 개인화 학습 (기획서 섹션 6.8)

POST /api/feedback — 사용자 피드백 기록 + 선호도 학습
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.preference_tracker import record_feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def post_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    try:
        feedback_count, learning_phase = await record_feedback(
            db=db,
            user_id=str(body.user_id),
            outfit_id=body.outfit_id,
            action=body.action,
        )
        return FeedbackResponse(
            status="ok",
            feedback_count=feedback_count,
            learning_phase=learning_phase,
        )
    except Exception:
        await db.rollback()
        logger.exception("feedback recording failed")
        raise HTTPException(status_code=500, detail="피드백 저장에 실패했습니다.")
