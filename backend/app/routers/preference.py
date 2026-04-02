"""Preference API — 취향 관리 (F-48, 8.4.11)

GET  /api/preference/{user_id}       — Style Seed + 피드백 학습 상태 조회
DELETE /api/preference/{user_id}/reset — 취향 초기화
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.preference import (
    PreferenceResetResponse,
    PreferenceStatusResponse,
    StyleSeedResponse,
)

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
