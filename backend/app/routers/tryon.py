"""Virtual Try-On API.

Gemini 나노바나나로 코디 착장 이미지를 생성한다.
무료 사용자 3회 제한, 프리미엄 무제한.
기획서 F-41, F-54 구현.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tryon import TryonGenerateRequest, TryonGenerateResponse, TryonUsageResponse
from app.services.usage_tracker import check_tryon_limit, increment_usage
from app.services.virtual_tryon import generate_tryon_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


@router.post("/generate", response_model=TryonGenerateResponse)
async def generate(
    req: TryonGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> TryonGenerateResponse:
    """착장 합성 이미지를 생성한다."""
    limit_info = await check_tryon_limit(db, req.user_id)
    if not limit_info["allowed"]:
        raise HTTPException(
            status_code=403,
            detail="무료 착장 생성 횟수를 모두 사용했어요. 프리미엄으로 업그레이드해주세요.",
        )

    try:
        result = await generate_tryon_image(
            db=db,
            outfit_id=req.outfit_id,
            user_id=req.user_id,
            closet_item_id=req.closet_item_id,
            model_image_url=req.model_image_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("착장 이미지 생성 실패")
        raise HTTPException(
            status_code=500,
            detail="이미지를 생성하지 못했어요. 다시 시도해주세요.",
        )

    if not result.get("cached"):
        await increment_usage(db, req.user_id)
        await db.commit()

    updated_limit = await check_tryon_limit(db, req.user_id)

    return TryonGenerateResponse(
        image_url=result["image_url"],
        outfit_id=result["outfit_id"],
        cached=result["cached"],
        remaining=updated_limit["remaining"],
    )


@router.get("/usage", response_model=TryonUsageResponse)
async def get_usage(
    user_id: Annotated[uuid.UUID, Query()],
    db: AsyncSession = Depends(get_db),
) -> TryonUsageResponse:
    """사용자의 착장 생성 잔여 횟수를 조회한다."""
    limit_info = await check_tryon_limit(db, user_id)
    return TryonUsageResponse(
        is_premium=limit_info["is_premium"],
        usage_count=limit_info["usage_count"],
        remaining=limit_info["remaining"],
    )
