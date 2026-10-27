"""Integration tests against a real PostgreSQL database.

Run with ``make test-integration`` (which applies migrations first) or
``uv run pytest -m integration`` after ``alembic upgrade head``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from silent_cinema.db.models import JobState, MediaAsset, ProcessingJob
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration


@pytest.fixture
def session(database_url: str) -> Iterator[Session]:
    engine = create_engine(database_url)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _media(session: Session, *, storage_key: str | None = None) -> MediaAsset:
    token = uuid4().hex
    asset = MediaAsset(
        original_filename="fixture.mp4",
        storage_key=storage_key or f"uploads/{token}/original.mp4",
        content_type="video/mp4",
        byte_size=1024,
        sha256=hashlib.sha256(token.encode()).hexdigest(),
    )
    session.add(asset)
    session.commit()
    return asset


def _job(media: MediaAsset, state: str = JobState.QUEUED) -> ProcessingJob:
    return ProcessingJob(media_asset_id=media.id, state=state)


def test_readiness_hits_real_database(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_migration_revision_is_recorded(session: Session) -> None:
    revision = session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert isinstance(revision, str)
    assert revision


def test_media_asset_defaults_and_uuid(session: Session) -> None:
    asset = _media(session)
    try:
        assert isinstance(asset.id, UUID)
        assert asset.probe_status == "pending"
        assert asset.created_at is not None
    finally:
        session.delete(asset)
        session.commit()


def test_media_asset_rejects_zero_byte_size(session: Session) -> None:
    token = uuid4().hex
    asset = MediaAsset(
        original_filename="empty.mp4",
        storage_key=f"uploads/{token}/original.mp4",
        content_type="video/mp4",
        byte_size=0,
        sha256=hashlib.sha256(token.encode()).hexdigest(),
    )
    session.add(asset)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_only_one_active_job_per_media(session: Session) -> None:
    asset = _media(session)
    try:
        session.add(_job(asset))
        session.commit()
        session.add(_job(asset))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.delete(asset)
        session.commit()


def test_completed_job_does_not_block_new_active_job(session: Session) -> None:
    asset = _media(session)
    try:
        session.add(_job(asset, JobState.COMPLETED))
        session.commit()
        session.add(_job(asset, JobState.QUEUED))
        session.commit()
    finally:
        session.delete(asset)
        session.commit()


def test_idempotency_key_is_unique_per_media(session: Session) -> None:
    asset = _media(session)
    try:
        first = _job(asset, JobState.COMPLETED)
        first.idempotency_key = "request-1"
        session.add(first)
        session.commit()

        second = _job(asset, JobState.COMPLETED)
        second.idempotency_key = "request-1"
        session.add(second)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.delete(asset)
        session.commit()


def test_job_rejects_invalid_state(session: Session) -> None:
    asset = _media(session)
    try:
        session.add(_job(asset, "unknown"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.delete(asset)
        session.commit()


def test_job_rejects_progress_out_of_range(session: Session) -> None:
    asset = _media(session)
    try:
        job = _job(asset)
        job.progress = 101
        session.add(job)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.delete(asset)
        session.commit()


def test_deleting_media_cascades_jobs(session: Session) -> None:
    asset = _media(session)
    job = _job(asset)
    session.add(job)
    session.commit()
    job_id = job.id

    session.delete(asset)
    session.commit()

    remaining = session.execute(
        text("SELECT count(*) FROM processing_jobs WHERE id = :job_id"), {"job_id": job_id}
    ).scalar_one()
    assert remaining == 0
