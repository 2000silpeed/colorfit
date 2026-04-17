"""사용자 계정 관리 API.

GET /api/user/{user_id} — 사용자 프로필 조회.
DELETE /api/user/{user_id} — 계정 삭제 (회원 탈퇴).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.closet_item import ClosetItem
from app.models.reaction import Reaction
from app.models.style_seed import StyleSeed
from app.models.subscription import Subscription
from app.models.tryon_cache import TryonCache
from app.models.tryon_usage import TryonUsage
from app.models.user import User
from app.models.user_preference import UserPreference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """사용자 프로필 조회."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="유효하지 않은 user_id 형식입니다")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return {
        "id": str(user.id),
        "email": user.email,
        "provider": user.provider,
        "gender": user.gender,
        "tone_id": user.tone_id,
        "tpo_primary": user.tpo_primary,
        "tpo_list": user.tpo_list or [],
        "style_moods": user.style_moods or [],
        "budget_min": user.budget_min,
        "budget_max": user.budget_max,
        "age_group": user.age_group,
        "is_premium": user.is_premium,
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """사용자 계정 + 관련 데이터 삭제."""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="유효하지 않은 user_id 형식입니다")

    exists_stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(exists_stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    try:
        for model in (
            ClosetItem,
            StyleSeed,
            Subscription,
            TryonCache,
            TryonUsage,
            UserPreference,
        ):
            await db.execute(delete(model).where(model.user_id == user_uuid))
        await db.execute(delete(Reaction).where(Reaction.user_id == str(user_uuid)))
        await db.execute(delete(User).where(User.id == user_uuid))
        await db.commit()
    except Exception:
        logger.exception("사용자 삭제 실패")
        await db.rollback()
        raise HTTPException(status_code=500, detail="계정 삭제 중 오류가 발생했습니다")

    return Response(status_code=204)
