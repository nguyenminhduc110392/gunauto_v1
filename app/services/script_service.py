from __future__ import annotations

from pathlib import Path

from app.models import InputType, NormalizedContent, VideoInput


class ScriptService:
    """Normalize every supported input into a title and a production-ready script.

    Replace the placeholder methods with real LLM, speech-to-text, and video-transcript
    providers. Keeping these operations in one service prevents provider-specific code
    from leaking into the pipeline.
    """

    async def normalize(self, source: VideoInput) -> NormalizedContent:
        if source.input_type is InputType.SCRIPT:
            return self._from_script(source)
        if source.input_type is InputType.TITLE_PROMPT:
            return await self._from_title_prompt(source)
        if source.input_type is InputType.SOURCE_VIDEO:
            return await self._from_source_video(source)
        if source.input_type is InputType.VOICE_FILE:
            return await self._from_voice_file(source)
        raise ValueError(f"Unsupported input type: {source.input_type}")

    def _from_script(self, source: VideoInput) -> NormalizedContent:
        script = (source.script or "").strip()
        title = source.title or self._derive_title(script)
        return NormalizedContent(title=title, script=script, language=source.profile.language)

    async def _from_title_prompt(self, source: VideoInput) -> NormalizedContent:
        script = await self.generate_article_script(
            title=source.title or "Untitled gun video",
            prompt=source.writing_prompt or "",
            language=source.profile.language,
        )
        return NormalizedContent(
            title=source.title or "Untitled gun video",
            script=script,
            language=source.profile.language,
        )

    async def _from_source_video(self, source: VideoInput) -> NormalizedContent:
        video_path = self._require_existing_file(source.source_video_path)
        transcript = await self.transcribe_media(video_path)
        rewritten = await self.rewrite_script(
            transcript=transcript,
            prompt=source.rewrite_prompt or "Rewrite clearly while preserving facts.",
            language=source.profile.language,
        )
        return NormalizedContent(
            title=self._derive_title(rewritten),
            script=rewritten,
            transcript=transcript,
            language=source.profile.language,
            source_video_path=video_path,
        )

    async def _from_voice_file(self, source: VideoInput) -> NormalizedContent:
        voice_path = self._require_existing_file(source.voice_file_path)
        transcript = await self.transcribe_media(voice_path)
        return NormalizedContent(
            title=self._derive_title(transcript),
            script=transcript,
            transcript=transcript,
            language=source.profile.language,
            source_voice_path=voice_path,
        )

    async def generate_article_script(self, title: str, prompt: str, language: str) -> str:
        # TODO: Call the configured LLM provider and return a fully written script.
        return f"{title}\n\n{prompt}\n\n[Generated article script placeholder in {language}]"

    async def rewrite_script(self, transcript: str, prompt: str, language: str) -> str:
        # TODO: Call the configured LLM provider with the original transcript and rewrite rules.
        return f"{prompt}\n\n{transcript}\n\n[Rewritten script placeholder in {language}]"

    async def transcribe_media(self, media_path: Path) -> str:
        # TODO: Connect Whisper or another speech-to-text provider.
        return f"[Transcript placeholder for {media_path.name}]"

    @staticmethod
    def _derive_title(text: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "Gun Video")
        return first_line[:120]

    @staticmethod
    def _require_existing_file(path: Path | None) -> Path:
        if path is None or not path.is_file():
            raise FileNotFoundError(f"Input media does not exist: {path}")
        return path
