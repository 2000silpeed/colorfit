from __future__ import annotations

from pydantic import BaseModel, Field


class StyleSeedResponse(BaseModel):
    mood_seed: str | None
    silhouette_seed: str | None
    color_seed: str | None
    price_seed: str | None
    seed_confidence: int | None


class PreferenceStatusResponse(BaseModel):
    style_seed: StyleSeedResponse | None
    feedback_count: int
    learning_target: int
    learning_phase: str
    has_seed: bool


class PreferenceResetRequest(BaseModel):
    mode: str = Field(..., pattern="^(all|feedback_only)$")


class PreferenceResetResponse(BaseModel):
    reset_mode: str
    message: str
