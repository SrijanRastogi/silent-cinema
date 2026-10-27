"""Unit tests for the native intertitle detector and interval grouping."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from silent_cinema.media.detector import DetectorConfig, OpenCvIntertitleDetector
from silent_cinema.media.pipeline import ScoredFrame, group_detections
from silent_cinema.media.timecode import format_timecode


def card_image() -> np.ndarray:
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(
        image,
        "THE LOST REEL",
        (120, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.6,
        (242, 234, 217),
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        "A silent film fragment",
        (150, 285),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (207, 197, 180),
        2,
        cv2.LINE_AA,
    )
    return image


def test_text_card_is_detected() -> None:
    analysis = OpenCvIntertitleDetector().analyse(card_image())

    assert analysis.is_intertitle is True
    assert analysis.reason == "ok"
    assert analysis.components >= 10
    assert 0 < analysis.score <= 1


def test_blank_dark_frame_is_rejected() -> None:
    analysis = OpenCvIntertitleDetector().analyse(np.zeros((480, 640, 3), dtype=np.uint8))

    assert analysis.is_intertitle is False
    assert analysis.reason == "no_foreground"
    assert analysis.score == 0


def test_bright_scene_is_rejected() -> None:
    gradient = np.tile(np.linspace(0, 255, 640, dtype=np.uint8), (480, 1))
    image = cv2.cvtColor(gradient, cv2.COLOR_GRAY2BGR)

    analysis = OpenCvIntertitleDetector().analyse(image)

    assert analysis.is_intertitle is False
    assert analysis.reason in {"too_much_foreground", "background_too_bright"}


def test_detector_config_is_documented_and_overridable() -> None:
    strict = DetectorConfig(min_components=500)
    analysis = OpenCvIntertitleDetector(strict).analyse(card_image())

    assert analysis.is_intertitle is False
    assert analysis.reason == "too_few_components"


def sample(timestamp_us: int, detected: bool, score: float = 0.8) -> ScoredFrame:
    return ScoredFrame(
        timestamp_us=timestamp_us,
        image_path=Path("frame.png"),
        is_intertitle=detected,
        score=score,
    )


def test_grouping_merges_consecutive_detections_and_splits_real_gaps() -> None:
    frames = [
        sample(0, True),
        sample(500_000, True),
        sample(1_000_000, True),
        sample(2_000_000, False),
        sample(3_000_000, False),
        sample(4_000_000, True),
        sample(4_500_000, True),
        sample(7_000_000, True),
    ]

    groups = group_detections(
        frames,
        sample_interval_us=500_000,
        max_gap_us=750_000,
        min_duration_us=400_000,
    )

    assert [group[0].timestamp_us for group in groups] == [0, 4_000_000, 7_000_000]
    assert groups[0][-1].timestamp_us == 1_000_000


def test_grouping_drops_intervals_below_minimum_duration() -> None:
    groups = group_detections(
        [sample(0, True)],
        sample_interval_us=200_000,
        max_gap_us=750_000,
        min_duration_us=400_000,
    )

    assert groups == []


def test_timecode_formatting_rounds_to_milliseconds() -> None:
    assert format_timecode(0) == "00:00:00.000"
    assert format_timecode(1_500_000) == "00:00:01.500"
    assert format_timecode(3_661_000_000) == "01:01:01.000"
