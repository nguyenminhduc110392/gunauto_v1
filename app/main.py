from __future__ import annotations

from fastapi import FastAPI, File, Form, UploadFile

from app.input_adapters import from_script, from_source_video, from_title_prompt, from_voice_file
from app.models import VideoManifest, VideoProfile
from app.pipeline import VideoPipeline

app = FastAPI(title="GunAuto V1", version="0.1.0")
pipeline = VideoPipeline()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/videos/from-script", response_model=VideoManifest)
async def create_from_script(
    script: str,
    title: str | None = None,
    template_name: str = "default",
    language: str = "en",
) -> VideoManifest:
    source = from_script(
        script=script,
        title=title,
        profile=VideoProfile(template_name=template_name, language=language),
    )
    return await pipeline.run(source)


@app.post("/videos/from-title-prompt", response_model=VideoManifest)
async def create_from_title_prompt(
    title: str,
    prompt: str,
    template_name: str = "default",
    language: str = "en",
) -> VideoManifest:
    source = from_title_prompt(
        title=title,
        prompt=prompt,
        profile=VideoProfile(template_name=template_name, language=language),
    )
    return await pipeline.run(source)


@app.post("/videos/from-source-video", response_model=VideoManifest)
async def create_from_source_video(
    video: UploadFile = File(...),
    rewrite_prompt: str = Form(...),
    template_name: str = Form("default"),
    language: str = Form("en"),
) -> VideoManifest:
    source = await from_source_video(
        video=video,
        rewrite_prompt=rewrite_prompt,
        profile=VideoProfile(template_name=template_name, language=language),
    )
    return await pipeline.run(source)


@app.post("/videos/from-voice", response_model=VideoManifest)
async def create_from_voice(
    voice: UploadFile = File(...),
    template_name: str = Form("default"),
    language: str = Form("en"),
) -> VideoManifest:
    source = await from_voice_file(
        voice=voice,
        profile=VideoProfile(template_name=template_name, language=language),
    )
    return await pipeline.run(source)
