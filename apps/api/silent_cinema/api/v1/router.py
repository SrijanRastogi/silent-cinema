"""Versioned API router."""

from fastapi import APIRouter

from silent_cinema.api.v1 import films, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(films.router)
