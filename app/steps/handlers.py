from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.enums import ArtifactType, InputType
from app.db.models import Artifact
from app.repositories.artifacts import ArtifactSpec, latest_artifact_uri
from app.services.storage import write_json_artifact, write_text_artifact
from app.steps.base import StepContext, StepResult


async def ingest_input(context: StepContext) -> StepResult:
    payload = context.project.input_payload
    input_type = InputType(context.project.input_type)
    artifacts: list[ArtifactSpec] = []

    if input_type == InputType.SOURCE_VIDEO:
        uri = str(payload["source_video_uri"])
        artifacts.append(ArtifactSpec(ArtifactType.SOURCE_VIDEO, uri, {"reused": True}))
    elif input_type == InputType.VOICE:
        uri = str(payload["voice_uri"])
        artifacts.append(ArtifactSpec(ArtifactType.SOURCE_VOICE, uri, {"reused": True}))

    return StepResult(output={"input_type": input_type.value, "accepted": True}, artifacts=artifacts)


async def transcribe_media(context: StepContext) -> StepResult:
    source_type = (
        ArtifactType.SOURCE_VIDEO
        if context.project.input_type == InputType.SOURCE_VIDEO
        else ArtifactType.SOURCE_VOICE
    )
    source_uri = await latest_artifact_uri(context.session, context.project.id, source_type)
    if not source_uri:
        raise RuntimeError(f"No source artifact found for {source_type}")

    transcript = (
        "[STT PLACEHOLDER] Replace app.steps.handlers.transcribe_media with the selected "
        f"speech-to-text provider. Source: {source_uri}"
    )
    uri = write_text_artifact(context.project.id, "transcript.txt", transcript)
    return StepResult(
        output={"provider": "placeholder", "source_uri": source_uri},
        artifacts=[ArtifactSpec(ArtifactType.TRANSCRIPT, uri)],
    )


async def prepare_script(context: StepContext) -> StepResult:
    payload = context.project.input_payload
    input_type = InputType(context.project.input_type)

    if input_type == InputType.SCRIPT:
        script = str(payload["script"]).strip()
        title = str(payload.get("title") or context.project.name)
    elif input_type == InputType.TITLE_PROMPT:
        title = str(payload["title"])
        script = (
            f"[LLM PLACEHOLDER]\nTitle: {title}\nWriting prompt: {payload['prompt']}\n"
            "Connect an LLM provider in this handler to generate the complete script."
        )
    else:
        transcript_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.TRANSCRIPT)
        if not transcript_uri:
            raise RuntimeError("Transcript artifact is missing")
        transcript = Path(transcript_uri).read_text(encoding="utf-8")
        title = str(payload.get("title") or context.project.name)
        rewrite_prompt = str(payload.get("prompt") or "Keep the meaning and rewrite for narration.")
        script = f"[REWRITE PLACEHOLDER]\nPrompt: {rewrite_prompt}\n\n{transcript}"

    uri = write_text_artifact(context.project.id, "script.txt", script)
    return StepResult(
        output={"title": title, "character_count": len(script), "provider": "placeholder"},
        artifacts=[ArtifactSpec(ArtifactType.SCRIPT, uri, {"title": title})],
    )


async def plan_scenes(context: StepContext) -> StepResult:
    script_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.SCRIPT)
    if not script_uri:
        raise RuntimeError("Script artifact is missing")
    script = Path(script_uri).read_text(encoding="utf-8")
    paragraphs = [part.strip() for part in script.split("\n\n") if part.strip()]
    scenes = [
        {
            "scene_number": index,
            "narration": paragraph,
            "visual_prompt": f"Create a compliant documentary-style firearm visual for scene {index}.",
            "template": "default",
        }
        for index, paragraph in enumerate(paragraphs or [script], start=1)
    ]
    uri = write_json_artifact(context.project.id, "scene_plan.json", scenes)
    return StepResult(
        output={"scene_count": len(scenes)},
        artifacts=[ArtifactSpec(ArtifactType.SCENE_PLAN, uri)],
    )


async def generate_voice(context: StepContext) -> StepResult:
    if context.project.input_type == InputType.VOICE:
        source_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.SOURCE_VOICE)
        if not source_uri:
            raise RuntimeError("Source voice artifact is missing")
        return StepResult(
            output={"provider": "reuse", "reused": True},
            artifacts=[ArtifactSpec(ArtifactType.VOICE, source_uri, {"reused": True})],
        )

    script_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.SCRIPT)
    placeholder = write_text_artifact(
        context.project.id,
        "voice.todo.txt",
        f"Generate TTS from script: {script_uri}\nProvider: placeholder",
    )
    return StepResult(
        output={"provider": "placeholder", "generated": False},
        artifacts=[ArtifactSpec(ArtifactType.VOICE, placeholder, {"placeholder": True})],
    )


async def collect_assets(context: StepContext) -> StepResult:
    scene_plan_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.SCENE_PLAN)
    manifest = {
        "provider": "placeholder",
        "scene_plan_uri": scene_plan_uri,
        "items": [],
        "note": "Connect image/video search or generation providers here.",
    }
    uri = write_json_artifact(context.project.id, "assets.json", manifest)
    return StepResult(
        output={"asset_count": 0, "provider": "placeholder"},
        artifacts=[ArtifactSpec(ArtifactType.ASSET_MANIFEST, uri)],
    )


async def generate_subtitles(context: StepContext) -> StepResult:
    script_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.SCRIPT)
    subtitle = "1\n00:00:00,000 --> 00:00:05,000\n[Subtitle timing placeholder]\n"
    uri = write_text_artifact(context.project.id, "subtitles.srt", subtitle)
    return StepResult(
        output={"provider": "placeholder", "script_uri": script_uri},
        artifacts=[ArtifactSpec(ArtifactType.SUBTITLES, uri, {"placeholder": True})],
    )


async def render_video(context: StepContext) -> StepResult:
    artifact_rows = list(
        await context.session.scalars(
            select(Artifact).where(Artifact.project_id == context.project.id).order_by(Artifact.created_at)
        )
    )
    manifest = {
        "renderer": "placeholder",
        "inputs": [{"type": item.artifact_type, "uri": item.uri} for item in artifact_rows],
        "note": "Connect FFmpeg/MoviePy and the template registry in this handler.",
    }
    manifest_uri = write_json_artifact(context.project.id, "render_request.json", manifest)
    output_uri = write_text_artifact(
        context.project.id,
        "video.todo.txt",
        f"Render request: {manifest_uri}",
    )
    return StepResult(
        output={"renderer": "placeholder", "rendered": False},
        artifacts=[ArtifactSpec(ArtifactType.VIDEO, output_uri, {"placeholder": True})],
    )


async def quality_check(context: StepContext) -> StepResult:
    video_uri = await latest_artifact_uri(context.session, context.project.id, ArtifactType.VIDEO)
    report = {
        "passed": bool(video_uri),
        "video_uri": video_uri,
        "checks": {"video_exists": bool(video_uri), "audio_present": None, "duration_valid": None},
    }
    uri = write_json_artifact(context.project.id, "qc_report.json", report)
    return StepResult(
        output={"passed": report["passed"]},
        artifacts=[ArtifactSpec(ArtifactType.QC_REPORT, uri)],
    )


async def finalize_manifest(context: StepContext) -> StepResult:
    artifacts = list(
        await context.session.scalars(
            select(Artifact).where(Artifact.project_id == context.project.id).order_by(Artifact.created_at)
        )
    )
    manifest: dict[str, Any] = {
        "project_id": str(context.project.id),
        "name": context.project.name,
        "input_type": context.project.input_type,
        "artifacts": [
            {"artifact_type": item.artifact_type, "uri": item.uri, "metadata": item.artifact_metadata}
            for item in artifacts
        ],
    }
    uri = write_json_artifact(context.project.id, "project_manifest.json", manifest)
    return StepResult(
        output={"artifact_count": len(artifacts), "manifest_uri": uri},
        artifacts=[ArtifactSpec(ArtifactType.PROJECT_MANIFEST, uri)],
    )
