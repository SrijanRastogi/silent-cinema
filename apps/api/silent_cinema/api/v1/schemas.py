"""Request and response models for the film workflow."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FilmSummary(BaseModel):
    """A film in the workspace, without its subtitle entries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str
    byte_size: int
    duration_us: int | None
    width: int | None
    height: int | None
    probe_status: str
    entry_count: int
    created_at: datetime


class SubtitleEntryRead(BaseModel):
    """One editable subtitle entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    start_us: int
    end_us: int
    text: str
    source: str
    review_status: str


class FilmDetail(FilmSummary):
    """A film with its editable subtitle entries."""

    entries: list[SubtitleEntryRead]
    track_id: UUID | None


class EntryUpdate(BaseModel):
    """Partial update for one subtitle entry."""

    text: str | None = Field(default=None, max_length=2000)
    start_us: int | None = Field(default=None, ge=0)
    end_us: int | None = Field(default=None, gt=0)


class EntryCreate(BaseModel):
    """Create a manual subtitle entry."""

    text: str = Field(min_length=1, max_length=2000)
    start_us: int = Field(ge=0)
    end_us: int = Field(gt=0)
