"""Shared test configuration.

Environment variables are set before importing the application so that the
module-level app factory can resolve settings without a local ``.env`` file.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://silent:silent_dev@127.0.0.1:5432/silent_cinema",
)

from silent_cinema.app import create_app
from silent_cinema.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


@pytest.fixture
def app(settings: Settings):  # type: ignore[no-untyped-def]
    return create_app(settings)


@pytest.fixture
def client(app):  # type: ignore[no-untyped-def]
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def database_url(settings: Settings) -> str:
    return settings.database_url
