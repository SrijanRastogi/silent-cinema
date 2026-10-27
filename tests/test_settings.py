"""Settings validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from silent_cinema.config import Settings


def test_defaults_are_declared(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://user:pass@127.0.0.1:5432/db",
    )
    assert settings.app_env == "development"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.max_upload_bytes == 2_147_483_648
    assert settings.stum_enabled is False
    assert settings.job_max_attempts == 3
    assert settings.allowed_video_extension_set == frozenset(
        {"mp4", "mkv", "mov", "avi", "mpg", "mpeg", "webm"}
    )


def test_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://other:secret@127.0.0.1:5433/other")
    monkeypatch.setenv("ALLOWED_VIDEO_EXTENSIONS", ".MP4, mkv ,,")
    settings = Settings(_env_file=None)
    assert settings.app_env == "test"
    assert settings.app_port == 9000
    assert settings.allowed_video_extension_set == frozenset({"mp4", "mkv"})


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:pass@127.0.0.1:5432/db",
        "mysql://user:pass@127.0.0.1:5432/db",
        "not-a-url",
    ],
)
def test_database_url_requires_psycopg_driver(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=url)


def test_invalid_app_env_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="staging",
            database_url="postgresql+psycopg://user:pass@127.0.0.1:5432/db",
        )


def test_invalid_port_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_port=70000,
            database_url="postgresql+psycopg://user:pass@127.0.0.1:5432/db",
        )
