"""사용량 추적 서비스.

사용자별 Virtual Try-On 사용 횟수를 추적하고 제한을 적용한다.
무료 사용자: 3회 제한, 프리미엄 사용자: 무제한.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tryon_usage import TryonUsage
from app.models.user import User

FREE_TRYON_LIMIT = 3


async def get_user_premium_status(
    db: AsyncSession, user_id: uuid.UUID
) -> bool:
    stmt = select(User.is_premium).where(User.id == user_id)
    result = await db.execute(stmt)
    is_premium = result.scalar_one_or_none()
    return bool(is_premium)


async def get_usage_count(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    stmt = select(TryonUsage.usage_count).where(TryonUsage.user_id == user_id)
    result = await db.execute(stmt)
    count = result.scalar_one_or_none()
    return count or 0


async def check_tryon_limit(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """사용 가능 여부를 확인한다.

    Returns:
        {
            "allowed": bool,
            "is_premium": bool,
            "usage_count": int,
            "remaining": int | None (프리미엄은 None),
        }
    """
    is_premium = await get_user_premium_status(db, user_id)

    if is_premium:
        return {
            "allowed": True,
            "is_premium": True,
            "usage_count": await get_usage_count(db, user_id),
            "remaining": None,
        }

    usage_count = await get_usage_count(db, user_id)
    remaining = max(0, FREE_TRYON_LIMIT - usage_count)

    return {
        "allowed": remaining > 0,
        "is_premium": False,
        "usage_count": usage_count,
        "remaining": remaining,
    }


async def check_and_increment(
    db: AsyncSession, user_id: uuid.UUID
) -> dict:
    """사용 가능 여부를 확인하고, 가능하면 원자적으로 1 증가시킨다.

    레이스 컨디션 방지: check + increment를 단일 트랜잭션에서 처리.

    Returns:
        {
            "allowed": bool,
            "is_premium": bool,
            "usage_count": int,
            "remaining": int | None,
        }
    """
    is_premium = await get_user_premium_status(db, user_id)

    if is_premium:
        new_count = await increment_usage(db, user_id)
        return {
            "allowed": True,
            "is_premium": True,
            "usage_count": new_count,
            "remaining": None,
        }

    stmt = (
        select(TryonUsage)
        .where(TryonUsage.user_id == user_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    usage = result.scalar_one_or_none()

    if usage:
        if usage.usage_count >= FREE_TRYON_LIMIT:
            return {
                "allowed": False,
                "is_premium": False,
                "usage_count": usage.usage_count,
                "remaining": 0,
            }
        usage.usage_count += 1
        await db.flush()
        remaining = max(0, FREE_TRYON_LIMIT - usage.usage_count)
        return {
            "allowed": True,
            "is_premium": False,
            "usage_count": usage.usage_count,
            "remaining": remaining,
        }

    usage = TryonUsage(user_id=user_id, usage_count=1)
    db.add(usage)
    await db.flush()
    return {
        "allowed": True,
        "is_premium": False,
        "usage_count": 1,
        "remaining": FREE_TRYON_LIMIT - 1,
    }


async def increment_usage(
    db: AsyncSession, user_id: uuid.UUID
) -> int:
    """사용 횟수를 1 증가시키고 현재 횟수를 반환한다."""
    stmt = select(TryonUsage).where(TryonUsage.user_id == user_id)
    result = await db.execute(stmt)
    usage = result.scalar_one_or_none()

    if usage:
        usage.usage_count += 1
    else:
        usage = TryonUsage(user_id=user_id, usage_count=1)
        db.add(usage)

    await db.flush()
    return usage.usage_count
