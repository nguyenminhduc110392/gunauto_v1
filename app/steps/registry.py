from __future__ import annotations

from app.core.enums import StepName
from app.steps.base import StepHandler
from app.steps.handlers import (
    collect_assets,
    finalize_manifest,
    generate_subtitles,
    generate_voice,
    ingest_input,
    plan_scenes,
    prepare_script,
    quality_check,
    render_video,
    transcribe_media,
)

STEP_HANDLERS: dict[StepName, StepHandler] = {
    StepName.INGEST_INPUT: ingest_input,
    StepName.TRANSCRIBE_MEDIA: transcribe_media,
    StepName.PREPARE_SCRIPT: prepare_script,
    StepName.PLAN_SCENES: plan_scenes,
    StepName.GENERATE_VOICE: generate_voice,
    StepName.COLLECT_ASSETS: collect_assets,
    StepName.GENERATE_SUBTITLES: generate_subtitles,
    StepName.RENDER_VIDEO: render_video,
    StepName.QUALITY_CHECK: quality_check,
    StepName.FINALIZE_MANIFEST: finalize_manifest,
}


def get_step_handler(step_name: str) -> StepHandler:
    try:
        return STEP_HANDLERS[StepName(step_name)]
    except (KeyError, ValueError) as exc:
        raise LookupError(f"No handler registered for step: {step_name}") from exc
