"""Virtual Try-On API.

Gemini 나노바나나로 코디 착장 이미지를 생성한다.
기획서 F-41, F-54 구현.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.tryon import TryonGenerateRequest, TryonGenerateResponse
from app.services.virtual_tryon import generate_tryon_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


@router.post("/generate", response_model=TryonGenerateResponse)
async def generate(
    req: TryonGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> TryonGenerateResponse:
    """착장 합성 이미지를 생성한다."""
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

    return TryonGenerateResponse(**result)
