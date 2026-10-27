"""Typed application settings loaded from the environment.

Secrets are never given defaults. ``DATABASE_URL`` must come from the
environment or a local ``.env`` file that is excluded from version control.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "test", "production"]


class Settings(BaseSettings):
    """Runtime configuration for the API and worker."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: AppEnv = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)

    database_url: str
    storage_root: Path = Path("./data")
    max_upload_bytes: int = Field(default=2_147_483_648, gt=0)
    allowed_video_extensions: str = "mp4,mkv,mov,avi,mpg,mpeg,webm"

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    tesseract_bin: str = "tesseract"
    ocr_default_language: str = "eng"

    worker_poll_interval_seconds: float = Field(default=2.0, gt=0)
    worker_lease_seconds: int = Field(default=120, ge=1)
    job_max_attempts: int = Field(default=3, ge=1, le=10)
    process_timeout_seconds: int = Field(default=900, ge=1)

    stum_enabled: bool = False
    stum_bin: str = "stum"

    log_level: str = "info"

    @field_validator("database_url")
    @classmethod
    def require_psycopg_url(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use the postgresql+psycopg:// driver")
        return value

    @property
    def allowed_video_extension_set(self) -> frozenset[str]:
        """Normalized extensions without leading dots."""
        values = {
            item.strip().lower().removeprefix(".")
            for item in self.allowed_video_extensions.split(",")
        }
        return frozenset(item for item in values if item)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    # Required fields are populated from the environment; MyPy cannot see that.
    return Settings()  # type: ignore[call-arg]
