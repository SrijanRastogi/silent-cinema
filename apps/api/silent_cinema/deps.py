"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from silent_cinema.config import Settings, get_settings
from silent_cinema.db.session import Database


def get_settings_dep() -> Settings:
    """Return process settings."""
    return get_settings()


def get_database(request: Request) -> Database:
    """Return the application's database owner, created during startup."""
    database = getattr(request.app.state, "database", None)
    if not isinstance(database, Database):
        raise RuntimeError("Database is not initialised")
    return database


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DatabaseDep = Annotated[Database, Depends(get_database)]
