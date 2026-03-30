import uuid

from sqlalchemy import Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    tone_preferences: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    category_preferences: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    brand_preferences: Mapped[dict | None] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    avg_liked_price: Mapped[int | None] = mapped_column(Integer)
    feedback_count: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))
    weight_overrides: Mapped[dict | None] = mapped_column(JSONB)
    updated_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
