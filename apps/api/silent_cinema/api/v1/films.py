"""Film upload, subtitle editing, playback, and export routes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from silent_cinema.api.v1.schemas import (
    EntryCreate,
    EntryUpdate,
    FilmDetail,
    FilmSummary,
    ScanRequest,
    SubtitleEntryRead,
)
from silent_cinema.db.session import Database
from silent_cinema.deps import SettingsDep, get_database
from silent_cinema.services import films

router = APIRouter(prefix="/films", tags=["films"])


def get_session(database: Annotated[Database, Depends(get_database)]) -> Iterator[Session]:
    with database.session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[FilmSummary])
def list_films(session: SessionDep) -> list[FilmSummary]:
    return films.list_films(session)


@router.post("", response_model=FilmDetail, status_code=status.HTTP_201_CREATED)
def upload_film(
    session: SessionDep,
    settings: SettingsDep,
    file: Annotated[UploadFile, File(description="A silent film video file")],
    ocr_language: Annotated[str, Form()] = "eng",
) -> FilmDetail:
    """Upload one film and process it synchronously with real detection and OCR.

    This request can take several minutes for a long film; no fake progress is
    reported. The worker queue in M3 replaces the synchronous call.
    """
    return films.create_film(
        session,
        settings,
        upload=file.file,
        filename=file.filename or "film.mp4",
        content_type=file.content_type or "application/octet-stream",
        ocr_language=ocr_language,
    )


@router.get("/{film_id}", response_model=FilmDetail)
def get_film(film_id: UUID, session: SessionDep) -> FilmDetail:
    return films.get_film_detail(session, film_id)


@router.patch("/{film_id}/entries/{entry_id}", response_model=SubtitleEntryRead)
def update_entry(
    film_id: UUID, entry_id: UUID, payload: EntryUpdate, session: SessionDep
) -> SubtitleEntryRead:
    return films.update_entry(session, film_id, entry_id, payload)


@router.post(
    "/{film_id}/entries",
    response_model=SubtitleEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entry(film_id: UUID, payload: EntryCreate, session: SessionDep) -> SubtitleEntryRead:
    return films.create_entry(session, film_id, payload)


@router.delete("/{film_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(film_id: UUID, entry_id: UUID, session: SessionDep) -> Response:
    films.delete_entry(session, film_id, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{film_id}/video")
def stream_video(film_id: UUID, session: SessionDep, settings: SettingsDep) -> FileResponse:
    asset = films.get_asset(session, film_id)
    path = films.video_path(settings, asset)
    return FileResponse(
        path,
        media_type=asset.content_type,
        filename=asset.original_filename,
        content_disposition_type="inline",
    )


@router.get("/{film_id}/subtitles/{subtitle_format}")
def download_subtitles(
    film_id: UUID,
    subtitle_format: Literal["srt", "vtt"],
    session: SessionDep,
    settings: SettingsDep,
) -> FileResponse:
    path = films.export_subtitles(session, settings, film_id, subtitle_format)
    media_type = "application/x-subrip" if subtitle_format == "srt" else "text/vtt"
    return FileResponse(
        path,
        media_type=media_type,
        filename=path.name,
        content_disposition_type="attachment",
    )


@router.get("/{film_id}/video-with-subtitles")
def download_muxed_video(
    film_id: UUID, session: SessionDep, settings: SettingsDep
) -> FileResponse:
    """Return a Matroska copy with a soft subtitle track (never burned in)."""
    path = films.mux_subtitles(session, settings, film_id)
    return FileResponse(
        path,
        media_type="video/x-matroska",
        filename=path.name,
        content_disposition_type="attachment",
    )


@router.get("/{film_id}/video-burned-subtitles")
def download_burned_video(
    film_id: UUID, session: SessionDep, settings: SettingsDep
) -> FileResponse:
    """Return an MP4 copy with subtitles permanently burned onto the video frames."""
    path = films.burn_subtitles(session, settings, film_id)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=path.name,
        content_disposition_type="attachment",
    )


@router.post("/{film_id}/scan", response_model=FilmDetail)
def scan_film(
    film_id: UUID,
    session: SessionDep,
    settings: SettingsDep,
    payload: ScanRequest | None = None,
) -> FilmDetail:
    """Scan or re-scan an existing stored film for intertitles and OCR."""
    ocr_language = payload.ocr_language if payload else "eng"
    return films.scan_film(session, settings, film_id, ocr_language=ocr_language)


__all__ = ["router"]
