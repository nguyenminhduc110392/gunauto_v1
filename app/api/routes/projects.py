from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.enums import ProjectStatus, StepStatus
from app.db.models import Project, StepRun
from app.repositories.projects import get_project, list_projects
from app.schemas.projects import ProjectCreate, ProjectRead
from app.workflows.scheduler import dispatch_ready_steps
from app.workflows.service import create_project_workflow

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreate, session: AsyncSession = Depends(get_session)) -> ProjectRead:
    project = await create_project_workflow(session, request)
    await dispatch_ready_steps(project.id)
    loaded = await get_project(session, project.id)
    if loaded is None:
        raise HTTPException(status_code=500, detail="Project was created but could not be reloaded")
    return ProjectRead.model_validate(loaded)


@router.get("", response_model=list[ProjectRead])
async def get_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[ProjectRead]:
    projects = await list_projects(session, limit=limit, offset=offset)
    return [ProjectRead.model_validate(item) for item in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_by_id(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> ProjectRead:
    project = await get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/cancel", response_model=ProjectRead)
async def cancel_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> ProjectRead:
    project = await session.get(Project, project_id, with_for_update=True)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.cancel_requested = True
    project.status = ProjectStatus.CANCELED
    await session.execute(
        update(StepRun)
        .where(
            StepRun.project_id == project_id,
            StepRun.status.in_([StepStatus.PENDING, StepStatus.QUEUED, StepStatus.RETRYING]),
        )
        .values(status=StepStatus.CANCELED)
    )
    await session.commit()
    loaded = await get_project(session, project_id)
    return ProjectRead.model_validate(loaded)


@router.post("/{project_id}/retry", response_model=ProjectRead)
async def retry_failed_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> ProjectRead:
    project = await session.get(Project, project_id, with_for_update=True)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.cancel_requested = False
    project.status = ProjectStatus.RUNNING
    project.error_message = None
    await session.execute(
        update(StepRun)
        .where(StepRun.project_id == project_id, StepRun.status == StepStatus.FAILED)
        .values(status=StepStatus.RETRYING, error_message=None)
    )
    await session.commit()
    await dispatch_ready_steps(project_id)
    loaded = await get_project(session, project_id)
    return ProjectRead.model_validate(loaded)


@router.post("/scheduler/dispatch")
async def dispatch_scheduler() -> dict[str, int]:
    return {"dispatched": await dispatch_ready_steps()}
