from __future__ import annotations

from pydantic import BaseModel


class ItemDetailResponse(BaseModel):
    id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    color_hex: str | None = None
    tone_id: str | None = None
    price: int | None = None
    mall_name: str | None = None
    mall_url: str | None = None
    image_url: str | None = None
    gender: str | None = None
    silhouette: str | None = None
    formality: int | None = None
    style_tag: str | None = None
    is_verified_brand: bool = False
    price_entries: list[PriceEntry] = []


class PriceEntry(BaseModel):
    mall_name: str
    price: int
    mall_url: str
    is_lowest: bool = False


class SimilarProductResponse(BaseModel):
    id: str
    name: str | None = None
    brand: str | None = None
    price: int | None = None
    image_url: str | None = None
    mall_url: str | None = None
    similarity: float
    match_type: str


class SimilarListResponse(BaseModel):
    source_id: str
    similar: list[SimilarProductResponse]


ItemDetailResponse.model_rebuild()
