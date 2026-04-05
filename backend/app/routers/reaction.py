from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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

        # ON CONFLICT DO NOTHING: 동시 요청으로 인한 중복 INSERT를 DB 레벨에서 차단.
        # UNIQUE 제약 위반 시 RETURNING은 아무 것도 반환하지 않는다.
        insert_stmt = (
            pg_insert(Reaction)
            .values(
                user_id=body.user_id,
                outfit_id=body.outfit_id,
                reaction_type=body.reaction_type,
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "outfit_id", "reaction_type"]
            )
            .returning(Reaction.id)
        )
        result = await db.execute(insert_stmt)
        inserted_id = result.scalar_one_or_none()
        await db.commit()

        if inserted_id is None:
            # 레이스 컨디션: 동일 요청이 이미 처리됨. 기존 레코드를 재조회해서 반환.
            existing = await db.execute(
                select(Reaction).where(
                    Reaction.user_id == body.user_id,
                    Reaction.outfit_id == body.outfit_id,
                    Reaction.reaction_type == body.reaction_type,
                )
            )
            row = existing.scalar_one_or_none()
            if row is None:
                raise HTTPException(status_code=500, detail="리액션 저장에 실패했습니다.")
            return ReactionResponse(
                id=row.id,
                user_id=str(row.user_id),
                outfit_id=row.outfit_id,
                reaction_type=row.reaction_type,
            )

        return ReactionResponse(
            id=inserted_id,
            user_id=body.user_id,
            outfit_id=body.outfit_id,
            reaction_type=body.reaction_type,
        )
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        logger.exception("reaction creation failed")
        raise HTTPException(status_code=500, detail="리액션 저장에 실패했습니다.")
