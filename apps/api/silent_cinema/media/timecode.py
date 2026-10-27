"""Timecode helpers shared by detection output and future subtitle export."""

from __future__ import annotations


def format_timecode(timestamp_us: int) -> str:
    """Render integer microseconds as ``HH:MM:SS.mmm``."""
    if timestamp_us < 0:
        raise ValueError("timestamp_us must not be negative")
    milliseconds = (timestamp_us + 500) // 1000
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
