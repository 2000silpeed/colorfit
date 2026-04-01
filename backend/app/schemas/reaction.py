from __future__ import annotations

from pydantic import BaseModel, Field


class ReactionRequest(BaseModel):
    user_id: str
    outfit_id: str
    reaction_type: str = Field(..., pattern="^(save|dislike)$")


class ReactionResponse(BaseModel):
    id: int
    user_id: str
    outfit_id: str
    reaction_type: str
