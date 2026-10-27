"""Detection pipeline: sample, group, score, and OCR intertitle cards."""

from __future__ import annotations

import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from silent_cinema.media.detector import IntertitleDetector, OpenCvIntertitleDetector
from silent_cinema.media.frames import sample_frames
from silent_cinema.media.ocr import OcrEngine, TesseractOcr
from silent_cinema.media.probe import MediaInfo, probe_media
from silent_cinema.media.process import MediaProcessError


@dataclass(frozen=True)
class DetectionOptions:
    """Tunables for sampling and interval merging."""

    sample_fps: float = 2.0
    max_gap_us: int = 1_500_000
    min_duration_us: int = 400_000
    ocr_language: str = "eng"


@dataclass(frozen=True)
class ScoredFrame:
    timestamp_us: int
    image_path: Path
    is_intertitle: bool
    score: float


@dataclass(frozen=True)
class IntertitleCandidate:
    """A detected interval with OCR text. Timestamps are integer microseconds."""

    start_us: int
    end_us: int
    text: str
    ocr_confidence: float
    detection_score: float
    frame_timestamp_us: int


@dataclass(frozen=True)
class DetectionResult:
    media: MediaInfo
    candidates: tuple[IntertitleCandidate, ...]
    sampled_frames: int


def group_detections(
    frames: Sequence[ScoredFrame],
    *,
    sample_interval_us: int,
    max_gap_us: int,
    min_duration_us: int,
) -> list[list[ScoredFrame]]:
    """Group detections separated by at most ``max_gap_us`` into intervals."""
    detected = sorted(
        (frame for frame in frames if frame.is_intertitle), key=lambda frame: frame.timestamp_us
    )
    groups: list[list[ScoredFrame]] = []
    for frame in detected:
        if groups and frame.timestamp_us - groups[-1][-1].timestamp_us <= max_gap_us:
            groups[-1].append(frame)
        else:
            groups.append([frame])

    kept: list[list[ScoredFrame]] = []
    for group in groups:
        start = group[0].timestamp_us
        end = group[-1].timestamp_us + sample_interval_us
        if end - start >= min_duration_us:
            kept.append(group)
    return kept


def detect_intertitles(
    video: Path,
    *,
    detector: IntertitleDetector | None = None,
    ocr: OcrEngine | None = None,
    options: DetectionOptions | None = None,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
    timeout_seconds: float = 900,
) -> DetectionResult:
    """Run native detection and OCR over a video file.

    The function performs real decoding and OCR. It makes no accuracy claim
    beyond the tested synthetic fixture.
    """
    options = options or DetectionOptions()
    detector = detector or OpenCvIntertitleDetector()
    ocr = ocr or TesseractOcr(language=options.ocr_language)
    if options.sample_fps <= 0:
        raise ValueError("sample_fps must be positive")

    media = probe_media(video, ffprobe_bin=ffprobe_bin, timeout_seconds=timeout_seconds)

    with tempfile.TemporaryDirectory(prefix="silent-cinema-frames-") as directory:
        sampled = sample_frames(
            video,
            Path(directory),
            sample_fps=options.sample_fps,
            ffmpeg_bin=ffmpeg_bin,
            timeout_seconds=timeout_seconds,
        )
        scored: list[ScoredFrame] = []
        for frame in sampled:
            image = cast(NDArray[np.uint8], cv2.imread(str(frame.image_path), cv2.IMREAD_COLOR))
            if image is None:
                raise MediaProcessError(
                    "frame_unreadable", f"Frame {frame.index} could not be decoded."
                )
            analysis = detector.analyse(image)
            scored.append(
                ScoredFrame(
                    timestamp_us=frame.timestamp_us,
                    image_path=frame.image_path,
                    is_intertitle=analysis.is_intertitle,
                    score=analysis.score,
                )
            )

        interval_us = round(1_000_000 / options.sample_fps)
        groups = group_detections(
            scored,
            sample_interval_us=interval_us,
            max_gap_us=options.max_gap_us,
            min_duration_us=options.min_duration_us,
        )

        candidates: list[IntertitleCandidate] = []
        for group in groups:
            best = max(group, key=lambda frame: (frame.score, -frame.timestamp_us))
            read = ocr.read(best.image_path)
            candidates.append(
                IntertitleCandidate(
                    start_us=group[0].timestamp_us,
                    end_us=group[-1].timestamp_us + interval_us,
                    text=read.text,
                    ocr_confidence=read.confidence,
                    detection_score=best.score,
                    frame_timestamp_us=best.timestamp_us,
                )
            )

    return DetectionResult(media=media, candidates=tuple(candidates), sampled_frames=len(sampled))
