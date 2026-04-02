from __future__ import annotations

from pydantic import BaseModel, Field


class ScoresResponse(BaseModel):
    pcf: float = 0.0
    of_: float = Field(0.0, alias="of")
    ch: float = 0.0
    pe: float = 0.0
    sf: float = 0.0

    model_config = {"populate_by_name": True}


class ProductBrief(BaseModel):
    id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    price: int | None = None
    image_url: str | None = None
    mall_url: str | None = None


class OutfitFeedItem(BaseModel):
    id: str
    gender: str | None = None
    designed_tpo: str | None = None
    total_price: int | None = None
    tags: list[str] | None = None
    scores: ScoresResponse | None = None
    soft_score: float = 0.0
    final_score: float = 0.0
    reasons: list[str] = []
    image_url: str | None = None


class FeedResponse(BaseModel):
    outfits: list[OutfitFeedItem]
    page: int
    page_size: int
    total: int
    has_next: bool


class TopPickResponse(BaseModel):
    id: str
    gender: str | None = None
    designed_tpo: str | None = None
    total_price: int | None = None
    tags: list[str] | None = None
    scores: ScoresResponse | None = None
    soft_score: float = 0.0
    final_score: float = 0.0
    reasons: list[str] = []
    highlight_reason: str = ""
    source: str = "db"  # "saved" | "db"
    image_url: str | None = None
    items: list[ProductBrief] = []


class OutfitDetailResponse(BaseModel):
    id: str
    gender: str | None = None
    designed_tpo: str | None = None
    designed_season: str | None = None
    designed_moods: list[str] | None = None
    total_price: int | None = None
    lowest_total_price: int | None = None
    is_complete_outfit: bool | None = None
    tags: list[str] | None = None
    scores: ScoresResponse | None = None
    reasons: list[str] | None = None
    items: list[ProductBrief] = []
