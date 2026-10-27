"""Film upload, detection, editing, and subtitle export services."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from silent_cinema.api.v1.schemas import (
    EntryCreate,
    EntryUpdate,
    FilmDetail,
    FilmSummary,
    SubtitleEntryRead,
)
from silent_cinema.config import Settings
from silent_cinema.db.models import (
    Intertitle,
    JobState,
    MediaAsset,
    ProbeStatus,
    ProcessingJob,
    SubtitleEntry,
    SubtitleTrack,
)
from silent_cinema.errors import AppError
from silent_cinema.media.ocr import OcrError
from silent_cinema.media.pipeline import DetectionOptions, detect_intertitles
from silent_cinema.media.probe import probe_media
from silent_cinema.media.process import MediaProcessError, run_tool, stderr_summary

CHUNK_SIZE = 1024 * 1024


def _now() -> datetime:
    return datetime.now(UTC)


def _summary(asset: MediaAsset, entry_count: int) -> FilmSummary:
    return FilmSummary(
        id=asset.id,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        byte_size=asset.byte_size,
        duration_us=asset.duration_us,
        width=asset.width,
        height=asset.height,
        probe_status=asset.probe_status,
        entry_count=entry_count,
        created_at=asset.created_at,
    )


def list_films(session: Session) -> list[FilmSummary]:
    """Return films newest first with real subtitle-entry counts."""
    rows = session.execute(
        select(MediaAsset, func.count(SubtitleEntry.id))
        .outerjoin(SubtitleTrack, SubtitleTrack.media_asset_id == MediaAsset.id)
        .outerjoin(SubtitleEntry, SubtitleEntry.track_id == SubtitleTrack.id)
        .where(MediaAsset.deleted_at.is_(None))
        .group_by(MediaAsset.id)
        .order_by(MediaAsset.created_at.desc())
    ).all()
    return [_summary(asset, int(count)) for asset, count in rows]


def get_asset(session: Session, film_id: uuid.UUID) -> MediaAsset:
    asset = session.scalar(
        select(MediaAsset).where(MediaAsset.id == film_id, MediaAsset.deleted_at.is_(None))
    )
    if asset is None:
        raise AppError("film_not_found", "The film was not found.", status_code=404)
    return asset


def get_track(session: Session, media_id: uuid.UUID) -> SubtitleTrack | None:
    return session.scalar(select(SubtitleTrack).where(SubtitleTrack.media_asset_id == media_id))


def _ensure_track(
    session: Session, asset: MediaAsset, language_tag: str | None = None
) -> SubtitleTrack:
    track = get_track(session, asset.id)
    if track is None:
        track = SubtitleTrack(
            media_asset_id=asset.id,
            name="OCR draft",
            source="ocr",
            language_tag=language_tag,
        )
        session.add(track)
        session.flush()
    return track


def get_entries(session: Session, track_id: uuid.UUID) -> list[SubtitleEntry]:
    return list(
        session.scalars(
            select(SubtitleEntry)
            .where(SubtitleEntry.track_id == track_id)
            .order_by(SubtitleEntry.sequence)
        )
    )


def get_film_detail(session: Session, film_id: uuid.UUID) -> FilmDetail:
    asset = get_asset(session, film_id)
    track = get_track(session, asset.id)
    entries = get_entries(session, track.id) if track else []
    summary = _summary(asset, len(entries))
    return FilmDetail(
        **summary.model_dump(),
        track_id=track.id if track else None,
        entries=[SubtitleEntryRead.model_validate(entry) for entry in entries],
    )


def _store_upload(
    upload: BinaryIO, filename: str, settings: Settings
) -> tuple[Path, str, int, str, str]:
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in settings.allowed_video_extension_set:
        raise AppError(
            "unsupported_media",
            "That file type is not supported. Use MP4, MKV, MOV, AVI, MPG, MPEG, or WebM.",
            status_code=415,
        )

    storage_dir = settings.storage_root / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_key = f"uploads/{uuid.uuid4().hex}.{extension}"
    destination = settings.storage_root / storage_key
    digest = hashlib.sha256()
    size = 0
    try:
        with destination.open("wb") as handle:
            while chunk := upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise AppError(
                        "upload_too_large",
                        f"The file exceeds the {settings.max_upload_bytes} byte limit.",
                        status_code=413,
                    )
                digest.update(chunk)
                handle.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise

    if size == 0:
        destination.unlink(missing_ok=True)
        raise AppError("invalid_media", "The uploaded file is empty.", status_code=422)
    return destination, storage_key, size, digest.hexdigest(), extension


def create_film(
    session: Session,
    settings: Settings,
    *,
    upload: BinaryIO,
    filename: str,
    content_type: str,
    ocr_language: str,
) -> FilmDetail:
    """Store, probe, detect, OCR, and persist one film synchronously.

    Synchronous processing is deliberate for the current local build: the UI
    shows a real pending request rather than invented progress. A durable
    worker queue replaces this in M3.
    """
    path, storage_key, size, sha256, _extension = _store_upload(upload, filename, settings)

    duplicate = session.scalar(
        select(MediaAsset).where(MediaAsset.sha256 == sha256, MediaAsset.deleted_at.is_(None))
    )
    if duplicate is not None:
        path.unlink(missing_ok=True)
        raise AppError("duplicate_media", "This film is already in the workspace.", status_code=409)

    try:
        media_info = probe_media(
            path,
            ffprobe_bin=settings.ffprobe_bin,
            timeout_seconds=settings.process_timeout_seconds,
        )
    except MediaProcessError as error:
        path.unlink(missing_ok=True)
        raise AppError("unsupported_media", error.message, status_code=415) from error

    asset = MediaAsset(
        original_filename=Path(filename).name,
        storage_key=storage_key,
        content_type=content_type or "application/octet-stream",
        byte_size=size,
        sha256=sha256,
        duration_us=media_info.duration_us,
        width=media_info.width,
        height=media_info.height,
        frame_rate_num=media_info.frame_rate_num,
        frame_rate_den=media_info.frame_rate_den,
        time_base_num=media_info.time_base_num,
        time_base_den=media_info.time_base_den,
        probe_status=ProbeStatus.OK,
    )
    session.add(asset)
    session.flush()

    job = ProcessingJob(
        media_asset_id=asset.id,
        state=JobState.OCR_PROCESSING,
        stage="detect_and_ocr",
        progress=25,
        started_at=_now(),
        config={"ocr_language": ocr_language},
    )
    session.add(job)
    session.flush()

    try:
        result = detect_intertitles(
            path,
            options=DetectionOptions(ocr_language=ocr_language),
            ffmpeg_bin=settings.ffmpeg_bin,
            ffprobe_bin=settings.ffprobe_bin,
            timeout_seconds=settings.process_timeout_seconds,
        )
    except (MediaProcessError, OcrError, ValueError) as error:
        message = getattr(error, "message", str(error))
        path.unlink(missing_ok=True)
        raise AppError(
            "processing_failed", f"Detection failed: {message}", status_code=422
        ) from error

    track = _ensure_track(session, asset, ocr_language)
    sequence = 0
    for candidate in result.candidates:
        intertitle = Intertitle(
            media_asset_id=asset.id,
            job_id=job.id,
            start_us=candidate.start_us,
            end_us=candidate.end_us,
            text=candidate.text,
            ocr_confidence=candidate.ocr_confidence,
            detector="native",
            detection_metadata={
                "detection_score": candidate.detection_score,
                "frame_timestamp_us": candidate.frame_timestamp_us,
            },
        )
        session.add(intertitle)
        session.flush()
        if not candidate.text:
            continue
        session.add(
            SubtitleEntry(
                track_id=track.id,
                sequence=sequence,
                start_us=candidate.start_us,
                end_us=candidate.end_us,
                text=candidate.text,
                source="ocr",
                source_intertitle_id=intertitle.id,
            )
        )
        sequence += 1

    job.state = JobState.COMPLETED
    job.stage = None
    job.progress = 100
    job.completed_at = _now()
    session.flush()
    return get_film_detail(session, asset.id)


def update_entry(
    session: Session, film_id: uuid.UUID, entry_id: uuid.UUID, payload: EntryUpdate
) -> SubtitleEntryRead:
    asset = get_asset(session, film_id)
    track = get_track(session, asset.id)
    if track is None:
        raise AppError("entry_not_found", "The subtitle entry was not found.", status_code=404)
    entry = session.scalar(
        select(SubtitleEntry).where(
            SubtitleEntry.id == entry_id, SubtitleEntry.track_id == track.id
        )
    )
    if entry is None:
        raise AppError("entry_not_found", "The subtitle entry was not found.", status_code=404)

    start_us = payload.start_us if payload.start_us is not None else entry.start_us
    end_us = payload.end_us if payload.end_us is not None else entry.end_us
    if end_us <= start_us:
        raise AppError("invalid_interval", "End time must be after start time.", status_code=422)
    if payload.text is not None and not payload.text.strip():
        raise AppError("empty_text", "Subtitle text cannot be empty.", status_code=422)

    clash = session.scalar(
        select(SubtitleEntry.id).where(
            SubtitleEntry.track_id == track.id,
            SubtitleEntry.id != entry.id,
            SubtitleEntry.start_us < end_us,
            SubtitleEntry.end_us > start_us,
        )
    )
    if clash is not None:
        raise AppError(
            "interval_overlap", "This timing overlaps another subtitle entry.", status_code=409
        )

    entry.start_us = start_us
    entry.end_us = end_us
    if payload.text is not None:
        entry.text = payload.text.strip()
    entry.review_status = "reviewed"
    session.flush()
    return SubtitleEntryRead.model_validate(entry)


def create_entry(session: Session, film_id: uuid.UUID, payload: EntryCreate) -> SubtitleEntryRead:
    asset = get_asset(session, film_id)
    if payload.end_us <= payload.start_us:
        raise AppError("invalid_interval", "End time must be after start time.", status_code=422)
    if not payload.text.strip():
        raise AppError("empty_text", "Subtitle text cannot be empty.", status_code=422)
    track = _ensure_track(session, asset)
    clash = session.scalar(
        select(SubtitleEntry.id).where(
            SubtitleEntry.track_id == track.id,
            SubtitleEntry.start_us < payload.end_us,
            SubtitleEntry.end_us > payload.start_us,
        )
    )
    if clash is not None:
        raise AppError(
            "interval_overlap", "This timing overlaps another subtitle entry.", status_code=409
        )
    highest = session.scalar(
        select(func.max(SubtitleEntry.sequence)).where(SubtitleEntry.track_id == track.id)
    )
    entry = SubtitleEntry(
        track_id=track.id,
        sequence=int(highest or -1) + 1,
        start_us=payload.start_us,
        end_us=payload.end_us,
        text=payload.text.strip(),
        source="manual",
        review_status="reviewed",
    )
    session.add(entry)
    session.flush()
    return SubtitleEntryRead.model_validate(entry)


def delete_entry(session: Session, film_id: uuid.UUID, entry_id: uuid.UUID) -> None:
    asset = get_asset(session, film_id)
    track = get_track(session, asset.id)
    if track is None:
        raise AppError("entry_not_found", "The subtitle entry was not found.", status_code=404)
    entry = session.scalar(
        select(SubtitleEntry).where(
            SubtitleEntry.id == entry_id, SubtitleEntry.track_id == track.id
        )
    )
    if entry is None:
        raise AppError("entry_not_found", "The subtitle entry was not found.", status_code=404)
    session.delete(entry)
    session.flush()


def _timestamp(us: int, separator: str) -> str:
    milliseconds = (us + 500) // 1000
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def render_subtitles(entries: list[SubtitleEntry], subtitle_format: str) -> str:
    """Render validated UTF-8 SRT or WebVTT from editable entries."""
    if not entries:
        raise AppError("no_subtitles", "There are no subtitle entries to export.", status_code=409)
    ordered = sorted(entries, key=lambda entry: (entry.start_us, entry.sequence))
    lines: list[str] = []
    if subtitle_format == "vtt":
        lines.append("WEBVTT")
        lines.append("")
    for index, entry in enumerate(ordered, start=1):
        separator = "," if subtitle_format == "srt" else "."
        if subtitle_format == "srt":
            lines.append(str(index))
        lines.append(
            f"{_timestamp(entry.start_us, separator)} --> {_timestamp(entry.end_us, separator)}"
        )
        lines.extend(entry.text.strip().splitlines())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def export_subtitles(
    session: Session, settings: Settings, film_id: uuid.UUID, subtitle_format: str
) -> Path:
    asset = get_asset(session, film_id)
    track = get_track(session, asset.id)
    entries = get_entries(session, track.id) if track else []
    content = render_subtitles(entries, subtitle_format)
    exports_dir = settings.storage_root / "exports" / str(asset.id)
    exports_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(asset.original_filename).stem).strip("-")
    path = exports_dir / f"{stem or 'subtitles'}.{subtitle_format}"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def video_path(settings: Settings, asset: MediaAsset) -> Path:
    path = settings.storage_root / asset.storage_key
    if not path.is_file():
        raise AppError("media_missing", "The stored film file is missing.", status_code=404)
    return path


def mux_subtitles(session: Session, settings: Settings, film_id: uuid.UUID) -> Path:
    """Attach a soft SRT track to a Matroska copy. Never burns text into frames."""
    asset = get_asset(session, film_id)
    srt_path = export_subtitles(session, settings, film_id, "srt")
    exports_dir = settings.storage_root / "exports" / str(asset.id)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(asset.original_filename).stem).strip("-")
    output = exports_dir / f"{stem or 'film'}-subtitled.mkv"
    track = get_track(session, asset.id)
    language = (track.language_tag if track and track.language_tag else None) or "und"
    result = run_tool(
        [
            settings.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path(settings, asset)),
            "-i",
            str(srt_path),
            "-map",
            "0",
            "-map",
            "1",
            "-c",
            "copy",
            "-c:s",
            "srt",
            "-metadata:s:s:0",
            f"language={language}",
            str(output),
        ],
        timeout_seconds=settings.process_timeout_seconds,
    )
    if result.returncode != 0:
        raise AppError(
            "mux_failed",
            f"FFmpeg could not attach subtitles: {stderr_summary(result)}",
            status_code=422,
        )
    return output


def burn_subtitles(session: Session, settings: Settings, film_id: uuid.UUID) -> Path:
    """Burn subtitles directly into frames using FFmpeg's subtitles filter. Produces an MP4."""
    asset = get_asset(session, film_id)
    srt_path = export_subtitles(session, settings, film_id, "srt")
    exports_dir = settings.storage_root / "exports" / str(asset.id)
    exports_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(asset.original_filename).stem).strip("-")
    output = exports_dir / f"{stem or 'film'}-burned-subtitles.mp4"
    escaped_srt = str(srt_path).replace("\\", "/").replace(":", "\\:")
    result = run_tool(
        [
            settings.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path(settings, asset)),
            "-vf",
            f"subtitles={escaped_srt}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            str(output),
        ],
        timeout_seconds=settings.process_timeout_seconds,
    )
    if result.returncode != 0:
        raise AppError(
            "burn_failed",
            f"FFmpeg could not burn subtitles: {stderr_summary(result)}",
            status_code=422,
        )
    return output


def scan_film(
    session: Session,
    settings: Settings,
    film_id: uuid.UUID,
    ocr_language: str = "eng",
) -> FilmDetail:
    """Scan or re-scan an existing stored film for intertitles and OCR."""
    asset = get_asset(session, film_id)
    path = video_path(settings, asset)

    track = _ensure_track(session, asset, ocr_language)
    existing_entries = session.scalars(
        select(SubtitleEntry).where(SubtitleEntry.track_id == track.id)
    ).all()
    for entry in existing_entries:
        session.delete(entry)

    existing_intertitles = session.scalars(
        select(Intertitle).where(Intertitle.media_asset_id == asset.id)
    ).all()
    for intertitle in existing_intertitles:
        session.delete(intertitle)
    session.flush()

    job = ProcessingJob(
        media_asset_id=asset.id,
        state=JobState.OCR_PROCESSING,
        stage="detect_and_ocr",
        progress=25,
        started_at=_now(),
        config={"ocr_language": ocr_language},
    )
    session.add(job)
    session.flush()

    try:
        result = detect_intertitles(
            path,
            options=DetectionOptions(ocr_language=ocr_language),
            ffmpeg_bin=settings.ffmpeg_bin,
            ffprobe_bin=settings.ffprobe_bin,
            timeout_seconds=settings.process_timeout_seconds,
        )
    except (MediaProcessError, OcrError, ValueError) as error:
        message = getattr(error, "message", str(error))
        raise AppError(
            "processing_failed", f"Detection failed: {message}", status_code=422
        ) from error

    sequence = 0
    for candidate in result.candidates:
        intertitle = Intertitle(
            media_asset_id=asset.id,
            job_id=job.id,
            start_us=candidate.start_us,
            end_us=candidate.end_us,
            text=candidate.text,
            ocr_confidence=candidate.ocr_confidence,
            detector="native",
            detection_metadata={
                "detection_score": candidate.detection_score,
                "frame_timestamp_us": candidate.frame_timestamp_us,
            },
        )
        session.add(intertitle)
        session.flush()
        if not candidate.text:
            continue
        session.add(
            SubtitleEntry(
                track_id=track.id,
                sequence=sequence,
                start_us=candidate.start_us,
                end_us=candidate.end_us,
                text=candidate.text,
                source="ocr",
                source_intertitle_id=intertitle.id,
            )
        )
        sequence += 1

    job.state = JobState.COMPLETED
    job.stage = None
    job.progress = 100
    job.completed_at = _now()
    session.flush()
    return get_film_detail(session, asset.id)

