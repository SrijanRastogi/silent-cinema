"""SQLAlchemy models for the M1 schema.

Only ``media_assets`` and ``processing_jobs`` exist in M1. Detection,
subtitle, and export tables arrive with their milestones; they are documented
in ``DATABASE.md`` but intentionally absent here.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from silent_cinema.db.base import Base


class ProbeStatus(StrEnum):
    PENDING = "pending"
    OK = "ok"
    FAILED = "failed"


class JobState(StrEnum):
    QUEUED = "queued"
    VALIDATING = "validating"
    DETECTING = "detecting"
    OCR_PROCESSING = "ocr_processing"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ACTIVE_JOB_STATES: tuple[JobState, ...] = (
    JobState.QUEUED,
    JobState.VALIDATING,
    JobState.DETECTING,
    JobState.OCR_PROCESSING,
    JobState.REVIEW_REQUIRED,
)

_ACTIVE_JOB_STATES_SQL = (
    "state IN ('queued','validating','detecting','ocr_processing','review_required')"
)


class MediaAsset(Base):
    """An uploaded film. Detection evidence and tracks reference this row."""

    __tablename__ = "media_assets"
    __table_args__ = (
        UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
        UniqueConstraint("sha256", name="uq_media_assets_sha256"),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        CheckConstraint("duration_us IS NULL OR duration_us > 0", name="duration_us_positive"),
        CheckConstraint("width IS NULL OR width > 0", name="width_positive"),
        CheckConstraint("height IS NULL OR height > 0", name="height_positive"),
        CheckConstraint(
            "frame_rate_num IS NULL OR frame_rate_num > 0", name="frame_rate_num_positive"
        ),
        CheckConstraint(
            "frame_rate_den IS NULL OR frame_rate_den > 0", name="frame_rate_den_positive"
        ),
        CheckConstraint(
            "time_base_num IS NULL OR time_base_num > 0", name="time_base_num_positive"
        ),
        CheckConstraint(
            "time_base_den IS NULL OR time_base_den > 0", name="time_base_den_positive"
        ),
        CheckConstraint("probe_status IN ('pending','ok','failed')", name="probe_status_valid"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    duration_us: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    frame_rate_num: Mapped[int | None] = mapped_column(Integer)
    frame_rate_den: Mapped[int | None] = mapped_column(Integer)
    time_base_num: Mapped[int | None] = mapped_column(Integer)
    time_base_den: Mapped[int | None] = mapped_column(Integer)
    probe_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=sql_text("'pending'")
    )
    probe_error_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    jobs: Mapped[list[ProcessingJob]] = relationship(
        back_populates="media_asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Intertitle(Base):
    """Immutable detection evidence produced by one processing job."""

    __tablename__ = "intertitles"
    __table_args__ = (
        CheckConstraint("start_us >= 0", name="start_non_negative"),
        CheckConstraint("end_us > start_us", name="interval_positive"),
        CheckConstraint(
            "review_status IN ('machine','reviewed','rejected')", name="review_status_valid"
        ),
        CheckConstraint("detector IN ('native','stum')", name="detector_valid"),
        UniqueConstraint("job_id", "start_us", "end_us", name="uq_intertitles_job_interval"),
        Index("ix_intertitles_media_asset_id_start_us", "media_asset_id", "start_us"),
        Index("ix_intertitles_job_id", "job_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    media_asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    detector: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("'native'"))
    detection_metadata: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=sql_text("'{}'::jsonb")
    )
    review_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=sql_text("'machine'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SubtitleTrack(Base):
    """An editable subtitle track. M1+ uses one OCR draft track per film."""

    __tablename__ = "subtitle_tracks"
    __table_args__ = (
        CheckConstraint("source IN ('ocr','manual')", name="source_valid"),
        CheckConstraint("status IN ('draft','reviewed','exported')", name="status_valid"),
        UniqueConstraint("media_asset_id", "name", name="uq_subtitle_tracks_media_name"),
        Index("ix_subtitle_tracks_media_asset_id", "media_asset_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    media_asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    language_tag: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("'ocr'"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("'draft'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SubtitleEntry(Base):
    """Editable subtitle text and timing. The single source of truth for export."""

    __tablename__ = "subtitle_entries"
    __table_args__ = (
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint("start_us >= 0", name="start_non_negative"),
        CheckConstraint("end_us > start_us", name="interval_positive"),
        CheckConstraint("source IN ('ocr','manual')", name="source_valid"),
        CheckConstraint("review_status IN ('machine','reviewed')", name="review_status_valid"),
        UniqueConstraint("track_id", "sequence", name="uq_subtitle_entries_track_sequence"),
        Index("ix_subtitle_entries_track_id_start_us", "track_id", "start_us"),
        Index("ix_subtitle_entries_source_intertitle_id", "source_intertitle_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    track_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subtitle_tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    start_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_us: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default=sql_text("'ocr'"))
    source_intertitle_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("intertitles.id", ondelete="SET NULL")
    )
    review_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=sql_text("'machine'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ProcessingJob(Base):
    """A durable unit of processing work, claimed by a worker."""

    __tablename__ = "processing_jobs"
    __table_args__ = (
        CheckConstraint(
            "state IN ('queued','validating','detecting','ocr_processing',"
            "'review_required','completed','failed','cancelled')",
            name="state_valid",
        ),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
        CheckConstraint("attempt >= 0", name="attempt_non_negative"),
        CheckConstraint("max_attempts BETWEEN 1 AND 10", name="max_attempts_range"),
        Index("ix_processing_jobs_state_run_after", "state", "run_after"),
        Index(
            "uq_processing_jobs_active_per_media",
            "media_asset_id",
            unique=True,
            postgresql_where=sql_text(_ACTIVE_JOB_STATES_SQL),
        ),
        Index(
            "uq_processing_jobs_media_idempotency",
            "media_asset_id",
            "idempotency_key",
            unique=True,
            postgresql_where=sql_text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()")
    )
    media_asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=sql_text("0")
    )
    config: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=sql_text("'{}'::jsonb")
    )
    attempt: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=sql_text("0"))
    max_attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=sql_text("3")
    )
    idempotency_key: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    recoverable: Mapped[bool | None] = mapped_column(Boolean)
    claimed_by: Mapped[str | None] = mapped_column(Text)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_after: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    media_asset: Mapped[MediaAsset] = relationship(back_populates="jobs")


# Descending indexes are declared after the mapped classes so the columns are
# available as expressions instead of strings.
Index("ix_media_assets_created_at_desc", MediaAsset.created_at.desc())
Index(
    "ix_processing_jobs_media_asset_created_at_desc",
    ProcessingJob.media_asset_id,
    ProcessingJob.created_at.desc(),
)
