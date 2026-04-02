import uuid

from sqlalchemy import ForeignKey, String, Integer, TIMESTAMP, text as sa_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    plan: Mapped[str] = mapped_column(String(20), nullable=False)  # "monthly" | "yearly"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=sa_text("'active'")
    )  # "active" | "cancelled" | "expired"
    coupon_code: Mapped[str | None] = mapped_column(String(50))
    price_krw: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa_text("NOW()")
    )
    expires_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
