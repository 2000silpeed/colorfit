from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.reaction import Reaction
from app.schemas.reaction import ReactionRequest, ReactionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reaction"])


@router.post("/reaction", response_model=ReactionResponse)
async def create_reaction(
    body: ReactionRequest,
    db: AsyncSession = Depends(get_db),
) -> ReactionResponse:
    try:
        existing = await db.execute(
            select(Reaction).where(
                Reaction.user_id == body.user_id,
                Reaction.outfit_id == body.outfit_id,
                Reaction.reaction_type == body.reaction_type,
            )
        )
        existing_row = existing.scalar_one_or_none()

        if existing_row is not None:
            await db.execute(
                delete(Reaction).where(Reaction.id == existing_row.id)
            )
            await db.commit()
            return ReactionResponse(
                id=existing_row.id,
                user_id=str(existing_row.user_id),
                outfit_id=existing_row.outfit_id,
                reaction_type=f"un{body.reaction_type}",
            )

        reaction = Reaction(
            user_id=body.user_id,
            outfit_id=body.outfit_id,
            reaction_type=body.reaction_type,
        )
        db.add(reaction)
        await db.commit()
        await db.refresh(reaction)

        return ReactionResponse(
            id=reaction.id,
            user_id=str(reaction.user_id),
            outfit_id=reaction.outfit_id,
            reaction_type=reaction.reaction_type,
        )
    except Exception:
        await db.rollback()
        logger.exception("reaction creation failed")
        raise HTTPException(status_code=500, detail="리액션 저장에 실패했습니다.")
