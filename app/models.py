from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class InputType(StrEnum):
    SCRIPT = "script"
    TITLE_PROMPT = "title_prompt"
    SOURCE_VIDEO = "source_video"
    VOICE_FILE = "voice_file"


class JobStatus(StrEnum):
    RECEIVED = "received"
    NORMALIZING = "normalizing"
    WRITING_SCRIPT = "writing_script"
    ANALYZING_AUDIO = "analyzing_audio"
    PLANNING_SCENES = "planning_scenes"
    GENERATING_VOICE = "generating_voice"
    COLLECTING_ASSETS = "collecting_assets"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoProfile(BaseModel):
    width: int = 1920
    height: int = 1080
    fps: int = 30
    aspect_ratio: str = "16:9"
    language: str = "en"
    target_duration_seconds: int | None = None
    template_name: str = "default"


class GunContentPolicy(BaseModel):
    channel_style: str = "US firearms review"
    fact_check_required: bool = True
    include_safety_note: bool = True
    prohibit_illegal_modification_guidance: bool = True
    prohibit_harmful_operational_guidance: bool = True


class VideoInput(BaseModel):
    input_type: InputType
    script: str | None = None
    title: str | None = None
    writing_prompt: str | None = None
    source_video_path: Path | None = None
    rewrite_prompt: str | None = None
    voice_file_path: Path | None = None
    profile: VideoProfile = Field(default_factory=VideoProfile)
    policy: GunContentPolicy = Field(default_factory=GunContentPolicy)

    @model_validator(mode="after")
    def validate_required_fields(self) -> "VideoInput":
        requirements = {
            InputType.SCRIPT: bool(self.script and self.script.strip()),
            InputType.TITLE_PROMPT: bool(self.title and self.writing_prompt),
            InputType.SOURCE_VIDEO: bool(self.source_video_path and self.rewrite_prompt),
            InputType.VOICE_FILE: bool(self.voice_file_path),
        }
        if not requirements[self.input_type]:
            raise ValueError(f"Missing required data for input_type={self.input_type}")
        return self


class NormalizedContent(BaseModel):
    title: str
    script: str
    language: str = "en"
    source_video_path: Path | None = None
    source_voice_path: Path | None = None
    transcript: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ScenePlan(BaseModel):
    scene_id: int
    narration: str
    visual_prompt: str
    duration_seconds: float
    template_name: str = "default"
    asset_paths: list[Path] = Field(default_factory=list)


class VideoManifest(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    status: JobStatus = JobStatus.RECEIVED
    input_type: InputType
    title: str | None = None
    script_path: Path | None = None
    voice_path: Path | None = None
    subtitle_path: Path | None = None
    output_video_path: Path | None = None
    scenes: list[ScenePlan] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
