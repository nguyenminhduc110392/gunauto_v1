from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import get_settings
from app.core.enums import ProjectStatus, StepStatus
from app.db.models import Project, StepDependency, StepRun
from app.db.session import AsyncSessionFactory
from app.workers.celery_app import celery_app

settings = get_settings()


@dataclass(frozen=True, slots=True)
class DispatchItem:
    step_id: uuid.UUID
    queue_name: str


async def _claim_ready_steps(session: AsyncSession, project_id: uuid.UUID | None) -> list[DispatchItem]:
    dependency_step = aliased(StepRun)
    incomplete_dependency = (
        select(StepDependency.step_run_id)
        .join(dependency_step, dependency_step.id == StepDependency.depends_on_step_run_id)
        .where(
            StepDependency.step_run_id == StepRun.id,
            dependency_step.status != StepStatus.COMPLETED,
        )
    )

    statement = (
        select(StepRun)
        .join(Project, Project.id == StepRun.project_id)
        .where(
            StepRun.status.in_([StepStatus.PENDING, StepStatus.RETRYING]),
            Project.cancel_requested.is_(False),
            Project.status.notin_([ProjectStatus.COMPLETED, ProjectStatus.CANCELED]),
            ~exists(incomplete_dependency),
        )
        .order_by(StepRun.created_at)
        .limit(settings.scheduler_batch_size)
        .with_for_update(skip_locked=True)
    )
    if project_id is not None:
        statement = statement.where(StepRun.project_id == project_id)

    steps = list(await session.scalars(statement))
    dispatch_items: list[DispatchItem] = []
    for step in steps:
        step.status = StepStatus.QUEUED
        dispatch_items.append(DispatchItem(step_id=step.id, queue_name=step.queue_name))

    if steps:
        project_ids = {step.project_id for step in steps}
        projects = list(await session.scalars(select(Project).where(Project.id.in_(project_ids))))
        for project in projects:
            if project.status == ProjectStatus.PENDING:
                project.status = ProjectStatus.RUNNING

    await session.commit()
    return dispatch_items


async def dispatch_ready_steps(project_id: uuid.UUID | None = None) -> int:
    async with AsyncSessionFactory() as session:
        items = await _claim_ready_steps(session, project_id)

    sent = 0
    for item in items:
        try:
            result = celery_app.send_task(
                "app.workers.tasks.execute_step",
                args=[str(item.step_id)],
                queue=item.queue_name,
            )
        except Exception as exc:
            async with AsyncSessionFactory() as session:
                step = await session.get(StepRun, item.step_id, with_for_update=True)
                if step is not None and step.status == StepStatus.QUEUED:
                    step.status = StepStatus.PENDING
                    step.error_message = f"Queue dispatch failed: {exc}"
                    await session.commit()
            continue

        async with AsyncSessionFactory() as session:
            step = await session.get(StepRun, item.step_id)
            if step is not None:
                step.celery_task_id = result.id
                await session.commit()
        sent += 1
    return sent
