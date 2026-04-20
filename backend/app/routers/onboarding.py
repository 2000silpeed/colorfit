"""Onboarding API — POST /api/onboarding

온보딩 5단계 결과를 받아 users + style_seeds 테이블에 저장한다.
기존 로그인 유저(user_id 전달)가 있으면 프로필 업데이트, 없으면 신규 생성.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.style_seed import StyleSeed
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.post("/onboarding", response_model=OnboardingResponse)
async def create_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    try:
        user: User | None = None

        # 기존 유저가 있으면 프로필 업데이트
        if body.user_id:
            try:
                existing_uuid = uuid.UUID(body.user_id)
                result = await db.execute(select(User).where(User.id == existing_uuid))
                user = result.scalar_one_or_none()
            except ValueError:
                logger.warning("invalid user_id in onboarding: %s", body.user_id)

        if user:
            # 기존 유저 프로필 업데이트
            user.gender = body.gender
            user.tone_id = body.tone_id
            user.age_group = body.age_group
            user.tpo_primary = body.tpo_list[0] if body.tpo_list else None
            user.tpo_secondary = body.tpo_list[1] if len(body.tpo_list) > 1 else None
            user.tpo_list = body.tpo_list or None
            user.style_moods = body.style_moods or None
            user.budget_min = body.budget_min
            user.budget_max = body.budget_max
            user_id = user.id
        else:
            # 신규 유저 생성
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                gender=body.gender,
                tone_id=body.tone_id,
                age_group=body.age_group,
                tpo_primary=body.tpo_list[0] if body.tpo_list else None,
                tpo_secondary=body.tpo_list[1] if len(body.tpo_list) > 1 else None,
                tpo_list=body.tpo_list or None,
                style_moods=body.style_moods or None,
                budget_min=body.budget_min,
                budget_max=body.budget_max,
            )
            db.add(user)

        if body.style_seeds:
            seed = StyleSeed(
                user_id=user_id,
                mood_seed=body.style_seeds.mood_seed,
                silhouette_seed=body.style_seeds.silhouette_seed,
                color_seed=body.style_seeds.color_seed,
                price_seed=body.style_seeds.price_seed,
                seed_confidence=body.seed_confidence,
            )
            db.add(seed)

        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("onboarding insert/update failed")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다")

    return OnboardingResponse(user_id=str(user_id))
