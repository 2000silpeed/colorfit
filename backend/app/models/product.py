from sqlalchemy import Boolean, String, Integer, SmallInteger, Text, ARRAY, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(20))
    color_hex: Mapped[str | None] = mapped_column(String(7))
    color_name: Mapped[str | None] = mapped_column(String(20))
    tone_id: Mapped[str | None] = mapped_column(String(30), index=True)
    price: Mapped[int | None] = mapped_column(Integer)
    mall_name: Mapped[str | None] = mapped_column(String(50))
    mall_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    gender: Mapped[str | None] = mapped_column(String(10), index=True)
    silhouette: Mapped[str | None] = mapped_column(String(20))
    formality: Mapped[int | None] = mapped_column(SmallInteger)
    age_group: Mapped[str | None] = mapped_column(String(10), index=True)
    style_tag: Mapped[str | None] = mapped_column(String(20), index=True)
    color_options: Mapped[list | None] = mapped_column(JSONB, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), index=True)
    last_observed_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
