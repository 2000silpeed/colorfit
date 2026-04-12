from __future__ import annotations

import uuid

from pydantic import BaseModel


class ColorOption(BaseModel):
    name: str
    hex: str


class TryonExtractColorsRequest(BaseModel):
    product_id: str
    image_url: str


class TryonExtractColorsResponse(BaseModel):
    product_id: str
    colors: list[ColorOption]


class TryonGenerateRequest(BaseModel):
    outfit_id: str
    user_id: uuid.UUID
    closet_item_id: uuid.UUID | None = None
    model_image_url: str | None = None
    color_overrides: dict[str, str] | None = None


class TryonGenerateResponse(BaseModel):
    image_url: str
    outfit_id: str
    cached: bool = False
    remaining: int | None = None


class TryonUsageResponse(BaseModel):
    is_premium: bool
    usage_count: int
    remaining: int | None = None
