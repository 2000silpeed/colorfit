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
from app.schemas.tryon import (
    TryonExtractColorsRequest,
    TryonExtractColorsResponse,
    TryonGenerateRequest,
    TryonGenerateResponse,
    TryonUsageResponse,
)
from app.services.usage_tracker import check_and_increment, check_tryon_limit, increment_usage
from app.services.virtual_tryon import (
    _get_default_model_bytes,
    extract_colors_from_product,
    generate_tryon_image,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tryon", tags=["tryon"])


@router.get("/_debug")
async def debug_model() -> dict:
    """진단용: 모델 이미지 로딩 상태 확인."""
    from pathlib import Path
    import os
    base = Path("/app/storage/models")
    files = {}
    if base.exists():
        for f in sorted(base.iterdir()):
            files[f.name] = f.stat().st_size
    bytes_data = await _get_default_model_bytes("female", None)
    sample = None
    if bytes_data:
        magic = bytes_data[:8].hex()
        sample = {"len": len(bytes_data), "magic_hex": magic, "is_png": bytes_data[:8] == b"\x89PNG\r\n\x1a\n"}
    return {
        "commit": os.environ.get("RENDER_GIT_COMMIT", "?")[:8],
        "supabase_url_set": bool(settings.supabase_url),
        "model_dir_exists": base.exists(),
        "model_files": files,
        "_get_default_model_bytes": sample,
    }


@router.post("/generate", response_model=TryonGenerateResponse)
async def generate(
    req: TryonGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> TryonGenerateResponse:
    """착장 합성 이미지를 생성한다."""
    # 먼저 제한 확인 (increment 없이)
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
            color_overrides=req.color_overrides,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("착장 이미지 생성 실패")
        raise HTTPException(
            status_code=500,
            detail="이미지를 생성하지 못했어요. 다시 시도해주세요.",
        )

    # 캐시 히트가 아닐 때만 사용량 차감
    remaining = limit_info["remaining"]
    if not result["cached"]:
        await increment_usage(db, req.user_id)
        if remaining is not None:
            remaining = max(0, remaining - 1)

    await db.commit()

    return TryonGenerateResponse(
        image_url=result["image_url"],
        outfit_id=result["outfit_id"],
        cached=result["cached"],
        remaining=remaining,
    )


@router.post("/extract-colors", response_model=TryonExtractColorsResponse)
async def extract_colors(req: TryonExtractColorsRequest) -> TryonExtractColorsResponse:
    """멀티컬러 상품 이미지에서 선택 가능한 색상 옵션을 추출한다."""
    try:
        colors = await extract_colors_from_product(req.image_url)
    except Exception:
        logger.exception("색상 추출 실패")
        raise HTTPException(
            status_code=500,
            detail="색상 옵션을 추출하지 못했어요.",
        )
    return TryonExtractColorsResponse(
        product_id=req.product_id,
        colors=[{"name": c["name"], "hex": c["hex"]} for c in colors],
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
