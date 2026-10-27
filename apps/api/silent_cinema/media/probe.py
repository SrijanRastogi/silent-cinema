"""Probe a video with ffprobe and expose integer-microsecond metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from silent_cinema.media.process import MediaProcessError, run_tool, stderr_summary


@dataclass(frozen=True)
class MediaInfo:
    """Validated properties of the first video stream."""

    duration_us: int
    width: int
    height: int
    frame_rate_num: int
    frame_rate_den: int
    time_base_num: int
    time_base_den: int


def _fraction(value: object, field: str) -> tuple[int, int]:
    if not isinstance(value, str) or "/" not in value:
        raise MediaProcessError("probe_invalid", f"ffprobe did not report a valid {field}.")
    numerator_text, denominator_text = value.split("/", 1)
    try:
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except ValueError as error:
        raise MediaProcessError(
            "probe_invalid", f"ffprobe reported a malformed {field}."
        ) from error
    if numerator <= 0 or denominator <= 0:
        raise MediaProcessError("probe_invalid", f"ffprobe reported a non-positive {field}.")
    return numerator, denominator


def _seconds_to_us(value: object) -> int:
    if not isinstance(value, (str, int, float)):
        raise MediaProcessError("probe_invalid", "ffprobe did not report a duration.")
    try:
        seconds = Decimal(str(value))
    except InvalidOperation as error:
        raise MediaProcessError(
            "probe_invalid", "ffprobe reported a malformed duration."
        ) from error
    if not seconds.is_finite() or seconds <= 0:
        raise MediaProcessError("probe_invalid", "ffprobe reported a non-positive duration.")
    return int((seconds * Decimal(1_000_000)).to_integral_value())


def probe_media(
    path: Path,
    *,
    ffprobe_bin: str = "ffprobe",
    timeout_seconds: float = 60,
) -> MediaInfo:
    """Read stream geometry, frame rate, time base, and duration.

    Raises:
        MediaProcessError: with a stable code when the file or stream is unusable.
    """
    if not path.is_file():
        raise MediaProcessError("media_missing", "The media file does not exist.")

    result = run_tool(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "format=duration:stream=width,height,avg_frame_rate,time_base",
            "-of",
            "json",
            str(path),
        ],
        timeout_seconds=timeout_seconds,
    )
    if result.returncode != 0:
        raise MediaProcessError(
            "probe_failed", f"ffprobe could not read the file: {stderr_summary(result)}"
        )

    try:
        payload = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MediaProcessError("probe_invalid", "ffprobe returned unreadable JSON.") from error

    streams = payload.get("streams") if isinstance(payload, dict) else None
    if not isinstance(streams, list) or not streams:
        raise MediaProcessError("probe_no_video", "The file has no video stream.")
    stream = streams[0]
    if not isinstance(stream, dict):
        raise MediaProcessError("probe_invalid", "ffprobe returned a malformed stream.")

    width = stream.get("width")
    height = stream.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise MediaProcessError("probe_invalid", "ffprobe did not report valid dimensions.")

    frame_rate_num, frame_rate_den = _fraction(stream.get("avg_frame_rate"), "frame rate")
    time_base_num, time_base_den = _fraction(stream.get("time_base"), "time base")

    duration_value = None
    format_section = payload.get("format")
    if isinstance(format_section, dict):
        duration_value = format_section.get("duration")
    if duration_value in {None, "N/A"}:
        duration_value = stream.get("duration")

    return MediaInfo(
        duration_us=_seconds_to_us(duration_value),
        width=width,
        height=height,
        frame_rate_num=frame_rate_num,
        frame_rate_den=frame_rate_den,
        time_base_num=time_base_num,
        time_base_den=time_base_den,
    )
