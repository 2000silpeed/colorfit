"""Tone API — GET /api/tone/{tone_id}

톤 상세 정보를 반환한다. 팔레트 JSON + 톤 설명 데이터를 병합.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.data.tone_descriptions import TONE_DESCRIPTIONS
from app.schemas.tone import ToneColor, ToneDetailResponse

router = APIRouter(prefix="/api", tags=["tone"])

PALETTES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palettes"

BEST_COLORS_COUNT = 6


def _load_palette(tone_id: str) -> dict:
    palette_path = PALETTES_DIR / f"{tone_id}.json"
    if not palette_path.exists():
        raise HTTPException(status_code=404, detail=f"톤 '{tone_id}'을(를) 찾을 수 없습니다")
    with open(palette_path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/tone/{tone_id}", response_model=ToneDetailResponse)
async def get_tone_detail(tone_id: str) -> ToneDetailResponse:
    palette = _load_palette(tone_id)

    desc_data = TONE_DESCRIPTIONS.get(tone_id)
    if desc_data is None:
        raise HTTPException(status_code=404, detail=f"톤 '{tone_id}'의 설명 데이터를 찾을 수 없습니다")

    all_colors = [
        ToneColor(hex=c["hex"], name_ko=c["name_ko"])
        for c in palette["colors"]
    ]

    best_colors = all_colors[:BEST_COLORS_COUNT]

    worst_colors = [
        ToneColor(**wc) for wc in desc_data["worst_colors"]
    ]

    return ToneDetailResponse(
        tone_id=palette["tone_id"],
        tone_name_ko=palette["tone_name_ko"],
        season=palette["season"],
        temperature=palette["temperature"],
        depth=palette["depth"],
        description=desc_data["description"],
        best_colors=best_colors,
        worst_colors=worst_colors,
        all_colors=all_colors,
    )
