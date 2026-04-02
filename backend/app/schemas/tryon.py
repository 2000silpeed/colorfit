from __future__ import annotations

import uuid

from pydantic import BaseModel


class TryonGenerateRequest(BaseModel):
    outfit_id: str
    user_id: uuid.UUID
    closet_item_id: uuid.UUID | None = None
    model_image_url: str | None = None


class TryonGenerateResponse(BaseModel):
    image_url: str
    outfit_id: str
    cached: bool = False
