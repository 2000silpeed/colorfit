import uuid

from sqlalchemy import Float, String, ARRAY, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClosetItem(Base):
    __tablename__ = "closet_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    dominant_color_hex: Mapped[str | None] = mapped_column(String(7))
    matched_tone_id: Mapped[str | None] = mapped_column(String(30))
    pcf_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float | None] = mapped_column(Float)
    reasons: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
