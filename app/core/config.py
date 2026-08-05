from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GunAuto V1"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://gunauto:gunauto@postgres:5432/gunauto"
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    storage_root: Path = Path("storage")
    max_upload_bytes: int = Field(default=2_147_483_648, ge=1)
    scheduler_batch_size: int = Field(default=100, ge=1, le=1000)
    default_step_max_attempts: int = Field(default=3, ge=1, le=10)

    llm_provider: str = "placeholder"
    stt_provider: str = "placeholder"
    tts_provider: str = "placeholder"
    asset_provider: str = "placeholder"
    render_provider: str = "placeholder"

    @property
    def uploads_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def projects_dir(self) -> Path:
        return self.storage_root / "projects"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.projects_dir.mkdir(parents=True, exist_ok=True)
    return settings
