from __future__ import annotations

from pydantic import BaseModel


class ToneColor(BaseModel):
    hex: str
    name_ko: str


class ToneDetailResponse(BaseModel):
    tone_id: str
    tone_name_ko: str
    season: str
    temperature: str
    depth: str
    description: str
    best_colors: list[ToneColor]
    worst_colors: list[ToneColor]
    all_colors: list[ToneColor]
