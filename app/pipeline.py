from __future__ import annotations

import json
from pathlib import Path

from app.config import settings
from app.models import JobStatus, VideoInput, VideoManifest
from app.services.production_services import (
    AssetService,
    RenderService,
    ScenePlanner,
    SubtitleService,
    VoiceService,
)
from app.services.script_service import ScriptService


class VideoPipeline:
    def __init__(
        self,
        script_service: ScriptService | None = None,
        scene_planner: ScenePlanner | None = None,
        voice_service: VoiceService | None = None,
        asset_service: AssetService | None = None,
        subtitle_service: SubtitleService | None = None,
        render_service: RenderService | None = None,
    ) -> None:
        self.script_service = script_service or ScriptService()
        self.scene_planner = scene_planner or ScenePlanner()
        self.voice_service = voice_service or VoiceService()
        self.asset_service = asset_service or AssetService()
        self.subtitle_service = subtitle_service or SubtitleService()
        self.render_service = render_service or RenderService()

    async def run(self, source: VideoInput) -> VideoManifest:
        manifest = VideoManifest(input_type=source.input_type)
        job_dir = settings.workspace_dir / "jobs" / str(manifest.job_id)
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            manifest.status = JobStatus.NORMALIZING
            self._save(manifest, job_dir)
            content = await self.script_service.normalize(source)
            manifest.title = content.title

            script_path = job_dir / "script.txt"
            script_path.write_text(content.script, encoding="utf-8")
            manifest.script_path = script_path

            manifest.status = JobStatus.PLANNING_SCENES
            manifest.scenes = await self.scene_planner.create_plan(content, source.profile)
            self._save(manifest, job_dir)

            manifest.status = JobStatus.GENERATING_VOICE
            manifest.voice_path = await self.voice_service.create_or_reuse_voice(content, job_dir)

            manifest.status = JobStatus.COLLECTING_ASSETS
            manifest.scenes = await self.asset_service.collect_assets(manifest.scenes, job_dir)
            manifest.subtitle_path = await self.subtitle_service.create_srt(manifest.scenes, job_dir)

            manifest.status = JobStatus.RENDERING
            self._save(manifest, job_dir)
            manifest.output_video_path = await self.render_service.render(manifest, source.profile, job_dir)

            manifest.status = JobStatus.COMPLETED
            self._save(manifest, job_dir)
            return manifest
        except Exception as exc:
            manifest.status = JobStatus.FAILED
            manifest.errors.append(f"{type(exc).__name__}: {exc}")
            self._save(manifest, job_dir)
            raise

    @staticmethod
    def _save(manifest: VideoManifest, job_dir: Path) -> None:
        (job_dir / "manifest.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
