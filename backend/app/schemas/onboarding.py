from __future__ import annotations

from pydantic import BaseModel, Field


class StyleSeedRequest(BaseModel):
    mood_seed: str | None = None
    silhouette_seed: str | None = None
    color_seed: str | None = None
    price_seed: str | None = None


class OnboardingRequest(BaseModel):
    gender: str = Field(..., pattern="^(male|female)$")
    tone_id: str = Field(..., min_length=1, max_length=30)
    tpo_list: list[str] = Field(default_factory=list, max_length=3)
    style_moods: list[str] = Field(default_factory=list, max_length=6)
    budget_min: int | None = Field(None, ge=0)
    budget_max: int | None = Field(None, ge=0)
    style_seeds: StyleSeedRequest | None = None
    seed_confidence: int | None = Field(None, ge=0, le=4)


class OnboardingResponse(BaseModel):
    user_id: str
