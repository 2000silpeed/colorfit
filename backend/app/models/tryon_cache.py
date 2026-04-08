import uuid

from sqlalchemy import String, Text, TIMESTAMP, text as sa_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TryonCache(Base):
    __tablename__ = "tryon_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    outfit_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    closet_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=False
    )
    profile_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa_text("NOW()")
    )
