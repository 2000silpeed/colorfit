from __future__ import annotations

from pydantic import BaseModel


class RecommendedProduct(BaseModel):
    id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    price: int | None = None
    image_url: str | None = None
    mall_url: str | None = None
    color_hex: str | None = None
    similarity: float
    match_reason: str


class TpoOutfitSuggestion(BaseModel):
    tpo: str
    tpo_label: str
    items: list[RecommendedProduct]


class ClosetRecommendationResponse(BaseModel):
    source_color_hex: str
    source_category: str
    user_tone_id: str
    recommendations: list[TpoOutfitSuggestion]
    total_count: int
