from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings
from app.models import NormalizedContent, ScenePlan, VideoManifest, VideoProfile


class ScenePlanner:
    async def create_plan(self, content: NormalizedContent, profile: VideoProfile) -> list[ScenePlan]:
        paragraphs = [p.strip() for p in content.script.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content.script]
        target = profile.target_duration_seconds or max(5, len(paragraphs) * 8)
        duration = target / max(1, len(paragraphs))
        return [
            ScenePlan(
                scene_id=index,
                narration=paragraph,
                visual_prompt=self._visual_prompt(paragraph, content.title),
                duration_seconds=duration,
                template_name=profile.template_name,
            )
            for index, paragraph in enumerate(paragraphs, start=1)
        ]

    @staticmethod
    def _visual_prompt(narration: str, title: str) -> str:
        return (
            f"Cinematic firearms review visual for '{title}'. "
            f"Illustrate this narration without showing unsafe handling: {narration[:300]}"
        )


class VoiceService:
    async def create_or_reuse_voice(self, content: NormalizedContent, job_dir: Path) -> Path:
        if content.source_voice_path:
            destination = job_dir / content.source_voice_path.name
            shutil.copy2(content.source_voice_path, destination)
            return destination
        output = job_dir / "voice.wav"
        # TODO: Replace with ElevenLabs/OpenAI TTS. This placeholder keeps the contract stable.
        output.write_bytes(b"")
        return output


class AssetService:
    async def collect_assets(self, scenes: list[ScenePlan], job_dir: Path) -> list[ScenePlan]:
        asset_dir = job_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        # TODO: Search licensed media, generate images, or reuse source-video clips.
        for scene in scenes:
            scene.asset_paths = []
        return scenes


class SubtitleService:
    async def create_srt(self, scenes: list[ScenePlan], job_dir: Path) -> Path:
        output = job_dir / "subtitles.srt"
        cursor = 0.0
        blocks: list[str] = []
        for scene in scenes:
            start = cursor
            end = cursor + scene.duration_seconds
            blocks.append(
                f"{scene.scene_id}\n{self._stamp(start)} --> {self._stamp(end)}\n{scene.narration}\n"
            )
            cursor = end
        output.write_text("\n".join(blocks), encoding="utf-8")
        return output

    @staticmethod
    def _stamp(seconds: float) -> str:
        milliseconds = int((seconds % 1) * 1000)
        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


class RenderService:
    async def render(self, manifest: VideoManifest, profile: VideoProfile, job_dir: Path) -> Path:
        output = settings.output_dir / f"{manifest.job_id}.mp4"
        # TODO: Compose scenes through MoviePy/FFmpeg and selected template modules.
        # A manifest sidecar is emitted now so pipeline output can already be inspected.
        sidecar = job_dir / "render_request.json"
        sidecar.write_text(
            json.dumps(
                {
                    "output": str(output),
                    "width": profile.width,
                    "height": profile.height,
                    "fps": profile.fps,
                    "template": profile.template_name,
                    "scene_count": len(manifest.scenes),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        output.touch()
        return output
