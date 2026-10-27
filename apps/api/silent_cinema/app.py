"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from silent_cinema import __version__
from silent_cinema.api.v1.router import api_router
from silent_cinema.config import Settings, get_settings
from silent_cinema.db.session import Database
from silent_cinema.errors import install_error_handlers
from silent_cinema.middleware import RequestIDMiddleware

DESCRIPTION = """\
Local-first intertitle extraction and subtitle review for silent films.

M1 exposes health and readiness only. Upload, processing, review, and export
endpoints arrive in later milestones; they are not stubbed or faked here.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured application instance."""
    resolved = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = Database(resolved.database_url)
        application.state.database = database
        try:
            yield
        finally:
            database.dispose()

    docs_enabled = resolved.app_env != "production"
    app = FastAPI(
        title="Silent Cinema in Your Language",
        description=DESCRIPTION,
        version=__version__,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs" if docs_enabled else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = resolved

    app.add_middleware(RequestIDMiddleware)
    if resolved.app_env == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )

    install_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
