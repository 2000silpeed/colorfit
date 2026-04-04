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
    style_tag: str | None = None
    is_verified_brand: bool = False


class FeedItemBrief(BaseModel):
    image_url: str | None = None
    category: str | None = None
    group: str | None = None
    brand: str | None = None
    style_tag: str | None = None
    is_verified_brand: bool = False


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
    items: list[FeedItemBrief] = []


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


class AxisComparison(BaseModel):
    axis: str
    axis_name: str
    score_a: float = 0.0
    score_b: float = 0.0
    diff: float = 0.0
    winner: str = "tie"


class DecisiveFactor(BaseModel):
    axis: str | None = None
    axis_name: str | None = None
    diff: float = 0.0
    winner: str | None = None
    explanation: str = ""


class OutfitBrief(BaseModel):
    id: str
    gender: str | None = None
    designed_tpo: str | None = None
    total_price: int | None = None
    scores: ScoresResponse | None = None
    image_url: str | None = None


class CompareResponse(BaseModel):
    outfit_a: OutfitBrief
    outfit_b: OutfitBrief
    axis_comparison: list[AxisComparison]
    total_a: float = 0.0
    total_b: float = 0.0
    winner: str = "tie"
    decisive_factor: DecisiveFactor


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
