from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import InputType


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    input_type: InputType
    title: str | None = None
    script: str | None = None
    prompt: str | None = None
    source_video_uri: str | None = None
    voice_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_input(self) -> "ProjectCreate":
        required: dict[InputType, tuple[str, ...]] = {
            InputType.SCRIPT: ("script",),
            InputType.TITLE_PROMPT: ("title", "prompt"),
            InputType.SOURCE_VIDEO: ("source_video_uri", "prompt"),
            InputType.VOICE: ("voice_uri",),
        }
        missing = [field for field in required[self.input_type] if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required fields for {self.input_type}: {', '.join(missing)}")
        return self

    def to_input_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"name", "input_type", "metadata"}, exclude_none=True)


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_name: str
    queue_name: str
    status: str
    attempt: int
    max_attempts: int
    output_payload: dict[str, Any]
    error_message: str | None
    celery_task_id: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_type: str
    uri: str
    artifact_metadata: dict[str, Any]
    created_at: datetime


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    input_type: str
    status: str
    input_payload: dict[str, Any]
    project_metadata: dict[str, Any]
    cancel_requested: bool
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[StepRead] = Field(default_factory=list)
    artifacts: list[ArtifactRead] = Field(default_factory=list)


class UploadResponse(BaseModel):
    uri: str
    original_filename: str
    size_bytes: int
    content_type: str | None
