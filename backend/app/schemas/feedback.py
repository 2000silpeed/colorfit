from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    user_id: uuid.UUID
    outfit_id: str
    action: str = Field(..., pattern="^(save|like|click|dislike)$")


class FeedbackResponse(BaseModel):
    status: str
    feedback_count: int
    learning_phase: str
