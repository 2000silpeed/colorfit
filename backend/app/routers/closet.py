"""내 옷장 분석 + 역방향 추천 + 옷장 목록 API.

옷 사진 업로드 → 퍼스널컬러 점수 + 이유.
보유 옷 기반 → TPO별 어울리는 아이템 추천.
옷장 전체 아이템 목록 + 퍼스널컬러 적합도 통계.
기획서 섹션 5.5.1, F-39 구현.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

import hashlib
import secrets
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.closet_item import ClosetItem
from app.schemas.closet import (
    ClosetAnalyzeRequest,
    ClosetAnalyzeResponse,
    ClosetItemAddRequest,
    ClosetItemAddResponse,
    ClosetItemResponse,
    ClosetListResponse,
    ClosetOutfitRequest,
    ClosetOutfitResponse,
    ClosetStats,
)
from app.schemas.closet_recommendation import (
    ClosetRecommendationResponse,
    RecommendedProduct,
    TpoOutfitSuggestion,
)
from app.models.user import User
from app.services.closet_analyzer import analyze_closet_item
from app.services.closet_outfit_matcher import match_outfits_for_closet_item
from app.services.closet_recommender import recommend_for_closet_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/closet", tags=["closet"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB
ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MIME_EXT = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp"}
CLOSET_STORAGE = Path(__file__).resolve().parents[2] / "storage" / "closet"
CLOSET_STORAGE.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_closet_image(request: Request, file: UploadFile = File(...)) -> dict:
    """옷장 사진 업로드 → storage/closet 파일 저장 후 /static URL 반환."""
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식: {file.content_type}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="이미지가 너무 커요 (최대 8MB)")
    # 컨텐츠 해시 + 랜덤 suffix로 파일명 생성 (동일 파일 중복 업로드 방지)
    ext = MIME_EXT[file.content_type]
    digest = hashlib.sha256(data).hexdigest()[:16]
    filename = f"{digest}_{secrets.token_hex(4)}.{ext}"
    filepath = CLOSET_STORAGE / filename
    filepath.write_bytes(data)
    base_url = str(request.base_url).rstrip("/")
    return {
        "image_url": f"{base_url}/static/closet/{filename}",
        "size": len(data),
        "content_type": file.content_type,
    }


@router.get("", response_model=ClosetListResponse)
async def get_closet(
    user_id: Annotated[uuid.UUID, Query()],
    db: AsyncSession = Depends(get_db),
) -> ClosetListResponse:
    """사용자 옷장 목록 + 퍼스널컬러 적합도 통계."""
    stmt = (
        select(ClosetItem)
        .where(ClosetItem.user_id == user_id)
        .order_by(ClosetItem.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    items = [
        ClosetItemResponse(
            id=str(row.id),
            image_url=row.image_url,
            category=row.category,
            dominant_color_hex=row.dominant_color_hex,
            matched_tone_id=row.matched_tone_id,
            pcf_score=row.pcf_score,
            overall_score=row.overall_score,
            reasons=row.reasons,
            created_at=str(row.created_at) if row.created_at else None,
        )
        for row in rows
    ]

    total_count = len(items)
    pcf_scores = [i.pcf_score for i in items if i.pcf_score is not None]
    average_pcf = sum(pcf_scores) / len(pcf_scores) if pcf_scores else 0.0
    good_count = sum(1 for s in pcf_scores if s >= 70)
    good_ratio = (good_count / total_count * 100) if total_count > 0 else 0.0

    stats = ClosetStats(
        total_count=total_count,
        average_pcf=round(average_pcf, 1),
        good_count=good_count,
        good_ratio=round(good_ratio, 1),
    )

    return ClosetListResponse(items=items, stats=stats)


@router.post("", response_model=ClosetItemAddResponse, status_code=201)
async def add_closet_item(
    req: ClosetItemAddRequest,
    db: AsyncSession = Depends(get_db),
) -> ClosetItemAddResponse:
    """사용자 옷장에 아이템 추가."""
    try:
        user_uuid = uuid.UUID(req.user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="유효하지 않은 user_id 형식입니다")

    item = ClosetItem(
        id=uuid.uuid4(),
        user_id=user_uuid,
        image_url=str(req.image_url),
        category=req.category,
        dominant_color_hex=req.dominant_color_hex,
        matched_tone_id=req.matched_tone_id,
        pcf_score=req.pcf_score,
        overall_score=req.overall_score,
        reasons=req.reasons,
    )
    db.add(item)
    try:
        await db.commit()
    except Exception:
        logger.exception("옷장 아이템 추가 실패")
        await db.rollback()
        raise HTTPException(status_code=500, detail="옷장 추가 중 오류가 발생했습니다")

    return ClosetItemAddResponse(id=str(item.id), message="옷장에 추가되었습니다")


@router.delete("/{item_id}")
async def delete_closet_item(
    item_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Query()],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """옷장 아이템 삭제."""
    stmt = select(ClosetItem).where(
        ClosetItem.id == item_id,
        ClosetItem.user_id == user_id,
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

    await db.delete(item)
    await db.commit()
    return {"message": "삭제되었습니다"}


@router.post("/analyze", response_model=ClosetAnalyzeResponse)
async def analyze_item(
    req: ClosetAnalyzeRequest,
) -> ClosetAnalyzeResponse:
    try:
        result = await analyze_closet_item(
            image_url=str(req.image_url),
            user_tone_id=req.user_tone_id,
        )
    except Exception:
        logger.exception("옷 분석 실패")
        raise HTTPException(status_code=500, detail="분석 중 오류가 발생했습니다")

    return ClosetAnalyzeResponse(**result)


@router.get("/recommendations", response_model=ClosetRecommendationResponse)
async def get_recommendations(
    color_hex: Annotated[str, Query(min_length=4, max_length=7)],
    category: str,
    user_tone_id: str,
    tpo: Annotated[str | None, Query()] = None,
    limit: int = Query(default=4, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
) -> ClosetRecommendationResponse:
    """보유 옷 기반 역방향 추천.

    사용자 옷의 색상/카테고리에 맞는 아이템을 TPO별로 추천한다.
    """
    if not color_hex.startswith("#"):
        color_hex = f"#{color_hex}"

    tpo_list = [t.strip() for t in tpo.split(",")] if tpo else None

    try:
        results = await recommend_for_closet_item(
            db=db,
            source_color_hex=color_hex,
            source_category=category,
            user_tone_id=user_tone_id,
            tpo_list=tpo_list,
            limit_per_tpo=limit,
        )
    except Exception:
        logger.exception("역방향 추천 실패")
        raise HTTPException(status_code=500, detail="추천 중 오류가 발생했습니다")

    suggestions = [
        TpoOutfitSuggestion(
            tpo=r["tpo"],
            tpo_label=r["tpo_label"],
            items=[RecommendedProduct(**item) for item in r["items"]],
        )
        for r in results
    ]

    total = sum(len(s.items) for s in suggestions)

    return ClosetRecommendationResponse(
        source_color_hex=color_hex,
        source_category=category,
        user_tone_id=user_tone_id,
        recommendations=suggestions,
        total_count=total,
    )


@router.post("/outfits", response_model=ClosetOutfitResponse)
async def get_closet_outfits(
    req: ClosetOutfitRequest,
    db: AsyncSession = Depends(get_db),
) -> ClosetOutfitResponse:
    """내 옷장 아이템 기반 코디 매칭 (F-57).

    단일 아이템: closet_item_id → 전략 A(DB 매칭) + B(동적 조합) fallback
    복수 아이템: closet_item_ids → 전략 B(동적 조합) 직행
    """
    try:
        user_uuid = uuid.UUID(req.user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="유효하지 않은 user_id 형식입니다")

    user = (await db.execute(
        select(User).where(User.id == user_uuid)
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    if not user.tone_id:
        raise HTTPException(status_code=422, detail="퍼스널컬러 진단이 필요합니다 (tone_id 없음)")

    try:
        result = await match_outfits_for_closet_item(
            db,
            closet_item_id=req.closet_item_id,
            closet_item_ids=req.closet_item_ids,
            user_id=req.user_id,
            user_tone_id=user.tone_id,
            gender=user.gender,
            age_group=user.age_group,
            tpo=req.tpo,
            budget_max=req.budget_max if req.budget_max is not None else user.budget_max,
            limit=req.limit,
        )
    except Exception:
        logger.exception("코디 매칭 실패")
        raise HTTPException(status_code=500, detail="코디 매칭 중 오류가 발생했습니다")

    return ClosetOutfitResponse(**result)
