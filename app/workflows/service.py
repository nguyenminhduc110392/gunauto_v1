from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import ProjectStatus, StepStatus
from app.db.models import Project, StepDependency, StepRun
from app.schemas.projects import ProjectCreate
from app.workflows.definitions import get_workflow, validate_workflow

settings = get_settings()


async def create_project_workflow(session: AsyncSession, request: ProjectCreate) -> Project:
    definitions = get_workflow(request.input_type)
    validate_workflow(definitions)

    project = Project(
        name=request.name,
        input_type=request.input_type.value,
        status=ProjectStatus.PENDING,
        input_payload=request.to_input_payload(),
        project_metadata=request.metadata,
    )
    session.add(project)
    await session.flush()

    step_by_name: dict[str, StepRun] = {}
    for definition in definitions:
        step = StepRun(
            project_id=project.id,
            step_name=definition.name.value,
            queue_name=definition.queue,
            status=StepStatus.PENDING,
            max_attempts=settings.default_step_max_attempts,
        )
        session.add(step)
        await session.flush()
        step_by_name[definition.name.value] = step

    dependencies: list[StepDependency] = []
    for definition in definitions:
        current = step_by_name[definition.name.value]
        for dependency in definition.depends_on:
            dependencies.append(
                StepDependency(
                    step_run_id=current.id,
                    depends_on_step_run_id=step_by_name[dependency.value].id,
                )
            )
    session.add_all(dependencies)
    await session.commit()
    return project
