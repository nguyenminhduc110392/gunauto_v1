from __future__ import annotations

from enum import StrEnum


class InputType(StrEnum):
    SCRIPT = "script"
    TITLE_PROMPT = "title_prompt"
    SOURCE_VIDEO = "source_video"
    VOICE = "voice"


class ProjectStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class StepStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class StepName(StrEnum):
    INGEST_INPUT = "ingest_input"
    TRANSCRIBE_MEDIA = "transcribe_media"
    PREPARE_SCRIPT = "prepare_script"
    PLAN_SCENES = "plan_scenes"
    GENERATE_VOICE = "generate_voice"
    COLLECT_ASSETS = "collect_assets"
    GENERATE_SUBTITLES = "generate_subtitles"
    RENDER_VIDEO = "render_video"
    QUALITY_CHECK = "quality_check"
    FINALIZE_MANIFEST = "finalize_manifest"


class ArtifactType(StrEnum):
    SOURCE_VIDEO = "source_video"
    SOURCE_VOICE = "source_voice"
    TRANSCRIPT = "transcript"
    SCRIPT = "script"
    SCENE_PLAN = "scene_plan"
    VOICE = "voice"
    ASSET_MANIFEST = "asset_manifest"
    SUBTITLES = "subtitles"
    VIDEO = "video"
    QC_REPORT = "qc_report"
    PROJECT_MANIFEST = "project_manifest"
