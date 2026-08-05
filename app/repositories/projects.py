from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Project


async def get_project(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    statement = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.steps), selectinload(Project.artifacts))
    )
    return await session.scalar(statement)


async def list_projects(session: AsyncSession, limit: int = 50, offset: int = 0) -> list[Project]:
    statement = (
        select(Project)
        .options(selectinload(Project.steps), selectinload(Project.artifacts))
        .order_by(Project.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.scalars(statement)).unique())
