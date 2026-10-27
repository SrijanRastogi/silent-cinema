"""Frame sampling with presentation timestamps taken from FFmpeg."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from silent_cinema.media.process import MediaProcessError, run_tool, stderr_summary

PTS_PATTERN = re.compile(r"pts_time:\s*([0-9.eE+-]+)")
FRAME_NAME = "frame-%06d.png"


@dataclass(frozen=True)
class SampledFrame:
    """A decoded frame and its presentation timestamp in microseconds."""

    index: int
    timestamp_us: int
    image_path: Path


def sample_frames(
    video: Path,
    output_dir: Path,
    *,
    sample_fps: float,
    ffmpeg_bin: str = "ffmpeg",
    timeout_seconds: float = 900,
) -> list[SampledFrame]:
    """Decode frames at ``sample_fps`` and map each PNG to its PTS.

    Timestamps come from FFmpeg's ``showinfo`` filter (``pts_time``), not from
    an assumed constant frame interval.
    """
    if sample_fps <= 0:
        raise ValueError("sample_fps must be positive")
    if not video.is_file():
        raise MediaProcessError("media_missing", "The media file does not exist.")
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_tool(
        [
            ffmpeg_bin,
            "-hide_banner",
            "-nostdin",
            "-nostats",
            "-i",
            str(video),
            "-vf",
            f"fps={sample_fps:g},showinfo",
            "-fps_mode",
            "vfr",
            str(output_dir / FRAME_NAME),
        ],
        timeout_seconds=timeout_seconds,
    )
    if result.returncode != 0:
        raise MediaProcessError(
            "decode_failed", f"FFmpeg could not decode frames: {stderr_summary(result)}"
        )

    stamps: list[int] = []
    for raw in PTS_PATTERN.findall(result.stderr.decode("utf-8", errors="replace")):
        try:
            seconds = Decimal(raw)
        except InvalidOperation as error:
            raise MediaProcessError(
                "timestamp_invalid", "FFmpeg returned a bad timestamp."
            ) from error
        if seconds < 0 or not seconds.is_finite():
            raise MediaProcessError("timestamp_invalid", "FFmpeg returned a bad timestamp.")
        stamps.append(int((seconds * Decimal(1_000_000)).to_integral_value()))

    images = sorted(output_dir.glob("frame-*.png"))
    if len(images) != len(stamps):
        raise MediaProcessError(
            "timestamp_mismatch",
            f"Decoded {len(images)} frames but read {len(stamps)} timestamps.",
        )
    if not images:
        raise MediaProcessError("no_frames", "FFmpeg produced no frames for this file.")

    return [
        SampledFrame(index=index, timestamp_us=timestamp, image_path=path)
        for index, (path, timestamp) in enumerate(zip(images, stamps, strict=True))
    ]
