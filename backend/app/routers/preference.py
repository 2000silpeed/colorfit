"""Preference API — 취향 관리 (F-48, 8.4.11)

GET  /api/preference/{user_id}       — Style Seed + 피드백 학습 상태 조회
DELETE /api/preference/{user_id}/reset — 취향 초기화
GET  /api/brands                     — 카테고리별 화이트리스트 브랜드 목록
GET  /api/preference/{user_id}/brands — 사용자 선호 브랜드 조회
PUT  /api/preference/{user_id}/brands — 사용자 선호 브랜드 저장
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.preference import (
    PreferenceResetResponse,
    PreferenceStatusResponse,
    StyleSeedResponse,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["preference"])

LEARNING_TARGET = 30


def _compute_learning_phase(feedback_count: int) -> str:
    if feedback_count == 0:
        return "seed"
    elif feedback_count < LEARNING_TARGET:
        return "hybrid"
    return "learned"


@router.get("/preference/{user_id}", response_model=PreferenceStatusResponse)
async def get_preference_status(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PreferenceStatusResponse:
    seed_row = (
        await db.execute(
            text(
                "SELECT mood_seed, silhouette_seed, color_seed, price_seed, seed_confidence "
                "FROM style_seeds WHERE user_id = :uid"
            ),
            {"uid": str(user_id)},
        )
    ).mappings().first()

    pref_row = (
        await db.execute(
            text(
                "SELECT feedback_count FROM user_preferences WHERE user_id = :uid"
            ),
            {"uid": str(user_id)},
        )
    ).mappings().first()

    style_seed = None
    if seed_row:
        style_seed = StyleSeedResponse(
            mood_seed=seed_row["mood_seed"],
            silhouette_seed=seed_row["silhouette_seed"],
            color_seed=seed_row["color_seed"],
            price_seed=seed_row["price_seed"],
            seed_confidence=seed_row["seed_confidence"],
        )

    feedback_count = pref_row["feedback_count"] if pref_row and pref_row["feedback_count"] else 0

    return PreferenceStatusResponse(
        style_seed=style_seed,
        feedback_count=feedback_count,
        learning_target=LEARNING_TARGET,
        learning_phase=_compute_learning_phase(feedback_count),
        has_seed=style_seed is not None,
    )


@router.delete("/preference/{user_id}/reset", response_model=PreferenceResetResponse)
async def reset_preference(
    user_id: uuid.UUID,
    mode: str = Query(..., pattern="^(all|feedback_only)$"),
    db: AsyncSession = Depends(get_db),
) -> PreferenceResetResponse:
    await db.execute(
        text("DELETE FROM reactions WHERE user_id = :uid"),
        {"uid": str(user_id)},
    )

    if mode == "all":
        await db.execute(
            text("DELETE FROM style_seeds WHERE user_id = :uid"),
            {"uid": str(user_id)},
        )
        await db.execute(
            text(
                "UPDATE user_preferences SET "
                "feedback_count = 0, "
                "tone_preferences = '{}'::jsonb, "
                "category_preferences = '{}'::jsonb, "
                "brand_preferences = '{}'::jsonb, "
                "avg_liked_price = NULL, "
                "weight_overrides = NULL, "
                "updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": str(user_id)},
        )
        message = "Style Seed 및 모든 학습 데이터가 초기화되었습니다."
    else:
        await db.execute(
            text(
                "UPDATE user_preferences SET "
                "feedback_count = 0, "
                "tone_preferences = '{}'::jsonb, "
                "category_preferences = '{}'::jsonb, "
                "brand_preferences = '{}'::jsonb, "
                "avg_liked_price = NULL, "
                "weight_overrides = NULL, "
                "updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": str(user_id)},
        )
        message = "피드백 학습 데이터가 초기화되었습니다. Style Seed는 유지됩니다."

    await db.commit()

    return PreferenceResetResponse(
        reset_mode=mode,
        message=message,
    )


# ── 브랜드 카테고리 그룹 (프론트 표시용) ──

BRAND_GROUPS: dict[str, list[str]] = {
    "SPA": [
        "무신사 스탠다드", "유니클로", "자라", "H&M", "갭", "올드네이비",
        "스파오", "탑텐", "에잇세컨즈", "미쏘", "풀앤베어", "지오다노",
    ],
    "컨템포러리": [
        "COS", "아르켓", "앤아더스토리즈", "마시모두띠", "띠어리",
        "클럽 모나코", "바나나리퍼블릭", "A.P.C.", "산드로", "마쥬",
        "시슬리", "바네사브루노", "이로", "빠투", "클로에",
    ],
    "트래디셔널": [
        "랄프로렌", "타미힐피거", "캘빈클라인", "라코스테", "빈폴",
        "폴로 랄프 로렌", "브룩스브라더스", "헤지스", "닥스",
        "마인드브릿지", "지이크", "올젠", "앤드지", "트루젠",
    ],
    "스트릿": [
        "커버낫", "디스이즈네버댓", "LMC", "예스아이씨", "칼하트",
        "스투시", "슈프림", "오프화이트", "팔라스", "아더에러",
        "앤더슨벨", "인사일런스", "로맨틱크라운", "마르디 메크르디",
        "키르시", "코드그라피",
    ],
    "스포츠/아웃도어": [
        "나이키", "아디다스", "뉴발란스", "컨버스", "반스", "푸마",
        "리복", "노스페이스", "파타고니아", "아크테릭스", "룰루레몬",
        "MLB", "휠라",
    ],
    "디자이너": [
        "아미", "아크네 스튜디오", "메종키츠네", "르메르", "이자벨마랑",
        "스톤아일랜드", "톰브라운", "이세이미야케", "꼼데가르송",
        "버버리", "막스마라",
    ],
    "럭셔리": [
        "셀린느", "보테가베네타", "구찌", "프라다", "생로랑",
        "발렌시아가", "디올", "루이비통", "에르메스", "로에베",
        "발렌티노", "지방시", "미우미우", "페라가모",
    ],
    "국내 디자이너": [
        "로우클래식", "닐바이피", "시스템", "에스제이와이피",
        "우영미", "준지", "마뗑킴", "럭키마르쉐", "오르시떼",
        "오아이오아이", "미니마리즘", "인스턴트펑크", "이벳필드", "노이어",
    ],
    "캐주얼/데님": [
        "리", "리바이스", "디젤", "그라미치", "폴햄", "프로젝트엠",
        "커스텀멜로우", "아베크롬비앤피치", "홀리스터",
        "마리떼 프랑소와 저버", "엘무드", "라퍼지스토어",
    ],
}


@router.get("/brands")
async def get_brand_list() -> dict:
    """카테고리별 화이트리스트 브랜드 목록."""
    return {"groups": BRAND_GROUPS}


@router.get("/preference/{user_id}/brands")
async def get_preferred_brands(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """사용자 선호 브랜드 조회."""
    row = (
        await db.execute(
            text("SELECT brand_preferences FROM user_preferences WHERE user_id = :uid"),
            {"uid": str(user_id)},
        )
    ).mappings().first()

    brands: list[str] = []
    if row and row["brand_preferences"]:
        prefs = row["brand_preferences"]
        brands = prefs.get("preferred", []) if isinstance(prefs, dict) else []

    return {"preferred_brands": brands}


@router.put("/preference/{user_id}/brands")
async def set_preferred_brands(
    user_id: uuid.UUID,
    brands: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """사용자 선호 브랜드 저장."""
    prefs_json = json.dumps({"preferred": brands}, ensure_ascii=False)

    # upsert
    result = await db.execute(
        text("SELECT id FROM user_preferences WHERE user_id = :uid"),
        {"uid": str(user_id)},
    )
    exists = result.first()

    if exists:
        await db.execute(
            text(
                "UPDATE user_preferences SET brand_preferences = :prefs::jsonb, updated_at = NOW() "
                "WHERE user_id = :uid"
            ),
            {"uid": str(user_id), "prefs": prefs_json},
        )
    else:
        await db.execute(
            text(
                "INSERT INTO user_preferences (user_id, brand_preferences) "
                "VALUES (:uid, :prefs::jsonb)"
            ),
            {"uid": str(user_id), "prefs": prefs_json},
        )

    await db.commit()
    return {"preferred_brands": brands, "count": len(brands)}
