"""Health and readiness endpoints."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from silent_cinema import __version__
from silent_cinema.deps import DatabaseDep
from silent_cinema.errors import ErrorEnvelope, request_id

logger = logging.getLogger("silent_cinema.health")

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Process liveness. Does not touch external dependencies."""

    status: Literal["ok"]
    version: str


class ReadinessResponse(BaseModel):
    """Dependency readiness. The database is checked on every request."""

    status: Literal["ready", "not_ready"]
    database: Literal["ok", "unavailable"]


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={500: {"model": ErrorEnvelope, "description": "Unexpected server error"}},
    summary="Liveness probe",
    description="Returns immediately if the API process is able to serve requests.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        503: {"model": ReadinessResponse, "description": "Database unavailable"},
        500: {"model": ErrorEnvelope, "description": "Unexpected server error"},
    },
    summary="Readiness probe",
    description="Executes a live SELECT 1 against PostgreSQL. Returns 503 when unavailable.",
)
def readiness(request: Request, response: Response, database: DatabaseDep) -> ReadinessResponse:
    try:
        database.ping()
    except SQLAlchemyError:
        logger.warning("Readiness check failed request_id=%s", request_id(request))
        response.status_code = 503
        return ReadinessResponse(status="not_ready", database="unavailable")
    return ReadinessResponse(status="ready", database="ok")
