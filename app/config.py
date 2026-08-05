from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GunAuto V1"
    app_env: str = "development"
    workspace_dir: Path = Path("workspace")
    output_dir: Path = Path("outputs")
    default_language: str = "en"
    default_video_width: int = 1920
    default_video_height: int = 1080
    default_fps: int = 30
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    tts_provider: str = "placeholder"
    tts_voice_id: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def prepare_directories(self) -> None:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.prepare_directories()
