from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

PlanType = Literal["monthly", "yearly"]


class SubscribeRequest(BaseModel):
    user_id: uuid.UUID
    plan: PlanType
    coupon_code: str | None = None


class SubscribeResponse(BaseModel):
    subscription_id: uuid.UUID
    plan: str
    status: str
    price_krw: int
    expires_at: datetime | None = None


class SubscriptionStatusResponse(BaseModel):
    is_premium: bool
    plan: str | None = None
    status: str | None = None
    expires_at: datetime | None = None
