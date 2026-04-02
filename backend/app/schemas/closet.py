from __future__ import annotations

from pydantic import BaseModel, HttpUrl, field_validator


class ClosetAnalyzeRequest(BaseModel):
    image_url: HttpUrl
    user_tone_id: str

    @field_validator("image_url")
    @classmethod
    def must_be_https(cls, v: HttpUrl) -> HttpUrl:
        if str(v).startswith("http://"):
            raise ValueError("https URL만 허용됩니다")
        return v


class ColorDetail(BaseModel):
    hex: str
    ratio: float


class ClosetAnalyzeResponse(BaseModel):
    dominant_colors: list[ColorDetail]
    matched_tone_id: str
    matched_tone_name: str
    pcf_score: float
    saturation_score: float
    lightness_score: float
    overall_score: float
    reasons: list[str]


class ClosetItemResponse(BaseModel):
    id: str
    image_url: str
    category: str | None = None
    dominant_color_hex: str | None = None
    matched_tone_id: str | None = None
    pcf_score: float | None = None
    overall_score: float | None = None
    reasons: list[str] | None = None
    created_at: str | None = None


class ClosetStats(BaseModel):
    total_count: int
    average_pcf: float
    good_count: int
    good_ratio: float


class ClosetListResponse(BaseModel):
    items: list[ClosetItemResponse]
    stats: ClosetStats
