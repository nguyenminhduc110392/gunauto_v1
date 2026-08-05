from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Artifact


@dataclass(slots=True)
class ArtifactSpec:
    artifact_type: str
    uri: str
    metadata: dict[str, Any] = field(default_factory=dict)


async def create_artifacts(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    step_run_id: uuid.UUID,
    specs: list[ArtifactSpec],
) -> list[Artifact]:
    artifacts = [
        Artifact(
            project_id=project_id,
            step_run_id=step_run_id,
            artifact_type=spec.artifact_type,
            uri=spec.uri,
            artifact_metadata=spec.metadata,
        )
        for spec in specs
    ]
    session.add_all(artifacts)
    await session.flush()
    return artifacts


async def latest_artifact_uri(
    session: AsyncSession, project_id: uuid.UUID, artifact_type: str
) -> str | None:
    statement = (
        select(Artifact.uri)
        .where(Artifact.project_id == project_id, Artifact.artifact_type == artifact_type)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )
    return await session.scalar(statement)
