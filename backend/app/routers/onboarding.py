"""Onboarding API — POST /api/onboarding

온보딩 5단계 결과를 받아 users + style_seeds 테이블에 저장한다.
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse)
async def create_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    user_id = str(uuid.uuid4())

    try:
        await db.execute(
            text("""
                INSERT INTO users (id, gender, tone_id, tpo_primary, tpo_secondary, tpo_list, style_moods, budget_min, budget_max)
                VALUES (:id, :gender, :tone_id, :tpo_primary, :tpo_secondary, :tpo_list, :style_moods, :budget_min, :budget_max)
            """),
            {
                "id": user_id,
                "gender": body.gender,
                "tone_id": body.tone_id,
                "tpo_primary": body.tpo_list[0] if body.tpo_list else None,
                "tpo_secondary": body.tpo_list[1] if len(body.tpo_list) > 1 else None,
                "tpo_list": json.dumps(body.tpo_list) if body.tpo_list else None,
                "style_moods": json.dumps(body.style_moods) if body.style_moods else None,
                "budget_min": body.budget_min,
                "budget_max": body.budget_max,
            },
        )

        if body.style_seeds:
            await db.execute(
                text("""
                    INSERT INTO style_seeds (user_id, mood_seed, silhouette_seed, color_seed, price_seed, seed_confidence)
                    VALUES (:user_id, :mood_seed, :silhouette_seed, :color_seed, :price_seed, :seed_confidence)
                """),
                {
                    "user_id": user_id,
                    "mood_seed": body.style_seeds.mood_seed,
                    "silhouette_seed": body.style_seeds.silhouette_seed,
                    "color_seed": body.style_seeds.color_seed,
                    "price_seed": body.style_seeds.price_seed,
                    "seed_confidence": body.seed_confidence,
                },
            )

        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("onboarding insert failed")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")

    return OnboardingResponse(user_id=user_id)
