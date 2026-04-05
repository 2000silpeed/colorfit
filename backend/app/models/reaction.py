from sqlalchemy import Integer, String, TIMESTAMP, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "outfit_id",
            "reaction_type",
            name="uq_reactions_user_outfit_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36))
    outfit_id: Mapped[str | None] = mapped_column(String(100))
    reaction_type: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
