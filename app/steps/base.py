from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, StepRun
from app.repositories.artifacts import ArtifactSpec


@dataclass(slots=True)
class StepContext:
    session: AsyncSession
    project: Project
    step: StepRun


@dataclass(slots=True)
class StepResult:
    output: dict[str, Any] = field(default_factory=dict)
    artifacts: list[ArtifactSpec] = field(default_factory=list)


class StepHandler(Protocol):
    async def __call__(self, context: StepContext) -> StepResult: ...
