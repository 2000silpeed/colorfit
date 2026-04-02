"""프리미엄 구독 서비스.

MVP: 테스트용 쿠폰 코드로 프리미엄 활성화.
정식 출시 시 결제 연동으로 교체 예정.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User

PLAN_PRICES = {
    "monthly": 4900,
    "yearly": 39000,
}

PLAN_DAYS = {
    "monthly": 30,
    "yearly": 365,
}

# MVP 테스트용 쿠폰 코드
VALID_COUPONS = {
    "COLORFIT-BETA",
    "PREMIUM-TEST",
}


async def subscribe(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan: str,
    coupon_code: str | None = None,
) -> dict:
    """구독을 생성하고 프리미엄을 활성화한다.

    MVP에서는 유효한 쿠폰 코드가 있어야 활성화된다.
    """
    if plan not in PLAN_PRICES:
        raise ValueError(f"유효하지 않은 플랜: {plan}")

    if not coupon_code or coupon_code.upper() not in VALID_COUPONS:
        raise ValueError("유효하지 않은 쿠폰 코드입니다.")

    # 기존 활성 구독 확인
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == "active",
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("이미 활성 구독이 있습니다.")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=PLAN_DAYS[plan])

    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        status="active",
        coupon_code=coupon_code.upper(),
        price_krw=PLAN_PRICES[plan],
        expires_at=expires_at,
    )
    db.add(subscription)

    # users.is_premium 플래그 업데이트
    await db.execute(
        sa_text("UPDATE users SET is_premium = true WHERE id = :uid"),
        {"uid": str(user_id)},
    )

    await db.flush()

    return {
        "subscription_id": subscription.id,
        "plan": subscription.plan,
        "status": subscription.status,
        "price_krw": subscription.price_krw,
        "expires_at": expires_at,
    }


async def get_subscription_status(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """사용자의 현재 구독 상태를 조회한다."""
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()

    if not sub:
        return {
            "is_premium": False,
            "plan": None,
            "status": None,
            "expires_at": None,
        }

    return {
        "is_premium": True,
        "plan": sub.plan,
        "status": sub.status,
        "expires_at": sub.expires_at,
    }
