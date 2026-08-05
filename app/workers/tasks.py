from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from celery import Task
from sqlalchemy import select

from app.core.enums import ProjectStatus, StepStatus
from app.db.models import Project, StepRun
from app.db.session import AsyncSessionFactory
from app.repositories.artifacts import create_artifacts
from app.steps.base import StepContext
from app.steps.registry import get_step_handler
from app.workers.celery_app import celery_app


async def _mark_retry(step_id: uuid.UUID, message: str) -> tuple[int, int]:
    async with AsyncSessionFactory() as session:
        step = await session.get(StepRun, step_id, with_for_update=True)
        if step is None:
            raise LookupError(f"Step {step_id} not found")
        step.error_message = message
        if step.attempt >= step.max_attempts:
            step.status = StepStatus.FAILED
            step.finished_at = datetime.now(UTC)
            project = await session.get(Project, step.project_id, with_for_update=True)
            if project is not None:
                project.status = ProjectStatus.FAILED
                project.error_message = f"Step {step.step_name} failed: {message}"
        else:
            step.status = StepStatus.RETRYING
        await session.commit()
        return step.attempt, step.max_attempts


async def _execute_step(step_id: uuid.UUID) -> None:
    async with AsyncSessionFactory() as session:
        step = await session.scalar(select(StepRun).where(StepRun.id == step_id).with_for_update())
        if step is None:
            raise LookupError(f"Step {step_id} not found")
        project = await session.get(Project, step.project_id, with_for_update=True)
        if project is None:
            raise LookupError(f"Project for step {step_id} not found")

        if project.cancel_requested:
            step.status = StepStatus.CANCELED
            step.finished_at = datetime.now(UTC)
            project.status = ProjectStatus.CANCELED
            await session.commit()
            return
        if step.status not in {StepStatus.QUEUED, StepStatus.RETRYING}:
            return

        step.status = StepStatus.RUNNING
        step.attempt += 1
        step.started_at = datetime.now(UTC)
        step.error_message = None
        await session.commit()

    async with AsyncSessionFactory() as session:
        step = await session.get(StepRun, step_id)
        if step is None:
            raise LookupError(f"Step {step_id} disappeared")
        project = await session.get(Project, step.project_id)
        if project is None:
            raise LookupError(f"Project for step {step_id} disappeared")

        handler = get_step_handler(step.step_name)
        result = await handler(StepContext(session=session, project=project, step=step))
        await create_artifacts(
            session,
            project_id=project.id,
            step_run_id=step.id,
            specs=result.artifacts,
        )
        step.output_payload = result.output
        step.status = StepStatus.COMPLETED
        step.finished_at = datetime.now(UTC)
        await session.commit()

    from app.workflows.scheduler import dispatch_ready_steps

    dispatched = await dispatch_ready_steps(project_id=project.id)
    if dispatched == 0:
        async with AsyncSessionFactory() as session:
            remaining = await session.scalar(
                select(StepRun.id)
                .where(
                    StepRun.project_id == project.id,
                    StepRun.status.notin_([StepStatus.COMPLETED, StepStatus.CANCELED]),
                )
                .limit(1)
            )
            if remaining is None:
                project_row = await session.get(Project, project.id, with_for_update=True)
                if project_row is not None and not project_row.cancel_requested:
                    project_row.status = ProjectStatus.COMPLETED
                    await session.commit()


@celery_app.task(bind=True, name="app.workers.tasks.execute_step", max_retries=10)
def execute_step(self: Task, step_id: str) -> None:
    parsed_id = uuid.UUID(step_id)
    try:
        asyncio.run(_execute_step(parsed_id))
    except Exception as exc:
        attempt, max_attempts = asyncio.run(_mark_retry(parsed_id, str(exc)))
        if attempt < max_attempts:
            raise self.retry(exc=exc, countdown=min(60, 2**attempt))
        raise


@celery_app.task(name="app.workers.tasks.dispatch_scheduler")
def dispatch_scheduler() -> int:
    from app.workflows.scheduler import dispatch_ready_steps

    return asyncio.run(dispatch_ready_steps())
