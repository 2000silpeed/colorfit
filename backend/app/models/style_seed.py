import uuid

from sqlalchemy import Integer, String, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StyleSeed(Base):
    __tablename__ = "style_seeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    mood_seed: Mapped[str | None] = mapped_column(String(30))
    silhouette_seed: Mapped[str | None] = mapped_column(String(30))
    color_seed: Mapped[str | None] = mapped_column(String(30))
    price_seed: Mapped[str | None] = mapped_column(String(30))
    seed_confidence: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
