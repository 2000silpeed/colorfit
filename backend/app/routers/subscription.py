"""프리미엄 구독 API.

POST /api/subscribe — 쿠폰 코드로 프리미엄 활성화
GET /api/subscription/status — 구독 상태 조회
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.subscription import (
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionStatusResponse,
)
from app.services.subscription import subscribe, get_subscription_status

router = APIRouter(prefix="/api", tags=["subscription"])


@router.post("/subscribe", response_model=SubscribeResponse)
async def create_subscription(
    req: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscribeResponse:
    """쿠폰 코드로 프리미엄 구독을 활성화한다."""
    try:
        result = await subscribe(db, req.user_id, req.plan, req.coupon_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()

    return SubscribeResponse(
        subscription_id=result["subscription_id"],
        plan=result["plan"],
        status=result["status"],
        price_krw=result["price_krw"],
        expires_at=result["expires_at"],
    )


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
async def subscription_status(
    user_id: Annotated[uuid.UUID, Query()],
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatusResponse:
    """사용자의 현재 구독 상태를 조회한다."""
    result = await get_subscription_status(db, user_id)
    return SubscriptionStatusResponse(**result)
