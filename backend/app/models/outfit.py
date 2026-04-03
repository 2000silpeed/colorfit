from sqlalchemy import String, Integer, SmallInteger, Boolean, Text, ARRAY, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Outfit(Base):
    __tablename__ = "outfits"
    __table_args__ = (
        Index("ix_outfits_designed_tpo", "designed_tpo"),
        Index("ix_outfits_gender", "gender"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    item_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    gender: Mapped[str | None] = mapped_column(String(10))
    designed_tpo: Mapped[str | None] = mapped_column(String(20))
    designed_season: Mapped[str | None] = mapped_column(String(10))
    designed_moods: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    total_price: Mapped[int | None] = mapped_column(Integer)
    lowest_total_price: Mapped[int | None] = mapped_column(Integer)
    is_complete_outfit: Mapped[bool | None] = mapped_column(Boolean)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    scores: Mapped[dict | None] = mapped_column(JSONB)
    style_details: Mapped[dict | None] = mapped_column(JSONB)
    reasons: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    llm_quality_score: Mapped[int | None] = mapped_column(SmallInteger)
