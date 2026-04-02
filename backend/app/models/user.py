import uuid

from sqlalchemy import Boolean, String, Integer, ARRAY, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10), index=True)
    tone_id: Mapped[str | None] = mapped_column(String(30), index=True)
    tpo_primary: Mapped[str | None] = mapped_column(String(20))
    tpo_secondary: Mapped[str | None] = mapped_column(String(20))
    tpo_list: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    style_moods: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    is_premium: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
