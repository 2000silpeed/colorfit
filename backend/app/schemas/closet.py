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
