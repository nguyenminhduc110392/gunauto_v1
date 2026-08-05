from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import StepRun


async def get_step(session: AsyncSession, step_id: uuid.UUID, *, for_update: bool = False) -> StepRun | None:
    statement = (
        select(StepRun)
        .where(StepRun.id == step_id)
        .options(selectinload(StepRun.project), selectinload(StepRun.dependencies))
    )
    if for_update:
        statement = statement.with_for_update()
    return await session.scalar(statement)
