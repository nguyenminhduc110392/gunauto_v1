from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.models import InputType, VideoInput, VideoProfile


def from_script(script: str, title: str | None = None, profile: VideoProfile | None = None) -> VideoInput:
    return VideoInput(
        input_type=InputType.SCRIPT,
        script=script,
        title=title,
        profile=profile or VideoProfile(),
    )


def from_title_prompt(title: str, prompt: str, profile: VideoProfile | None = None) -> VideoInput:
    return VideoInput(
        input_type=InputType.TITLE_PROMPT,
        title=title,
        writing_prompt=prompt,
        profile=profile or VideoProfile(),
    )


async def save_upload(upload: UploadFile, category: str) -> Path:
    suffix = Path(upload.filename or "upload.bin").suffix
    destination_dir = settings.workspace_dir / "uploads" / category
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{uuid4().hex}{suffix}"
    with destination.open("wb") as target:
        shutil.copyfileobj(upload.file, target)
    await upload.close()
    return destination


async def from_source_video(
    video: UploadFile,
    rewrite_prompt: str,
    profile: VideoProfile | None = None,
) -> VideoInput:
    path = await save_upload(video, "videos")
    return VideoInput(
        input_type=InputType.SOURCE_VIDEO,
        source_video_path=path,
        rewrite_prompt=rewrite_prompt,
        profile=profile or VideoProfile(),
    )


async def from_voice_file(voice: UploadFile, profile: VideoProfile | None = None) -> VideoInput:
    path = await save_upload(voice, "voices")
    return VideoInput(
        input_type=InputType.VOICE_FILE,
        voice_file_path=path,
        profile=profile or VideoProfile(),
    )
