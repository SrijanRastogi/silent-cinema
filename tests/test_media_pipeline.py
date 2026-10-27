"""Media tests: real FFmpeg decode, detection, and Tesseract OCR.

Marked ``media`` because they require FFmpeg and Tesseract.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from silent_cinema.media.pipeline import DetectionOptions, detect_intertitles
from silent_cinema.media.probe import MediaInfo, probe_media
from silent_cinema.media.timecode import format_timecode

from scripts.generate_fixture import generate

pytestmark = pytest.mark.media


@pytest.fixture(scope="module")
def fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("fixture")
    return generate(directory / "synthetic-intertitles.mp4")


def test_probe_reads_real_stream_metadata(fixture: Path) -> None:
    media: MediaInfo = probe_media(fixture)

    assert (media.width, media.height) == (640, 480)
    assert 17_500_000 <= media.duration_us <= 18_500_000
    assert media.frame_rate_num / media.frame_rate_den == pytest.approx(10.0)
    assert media.time_base_num > 0 and media.time_base_den > 0


def test_detection_and_ocr_produce_the_three_known_cards(fixture: Path) -> None:
    result = detect_intertitles(
        fixture,
        options=DetectionOptions(sample_fps=2.0, ocr_language="eng"),
    )

    assert result.sampled_frames >= 34
    assert len(result.candidates) == 3

    texts = [candidate.text.upper() for candidate in result.candidates]
    assert "LOST" in texts[0] and "REEL" in texts[0]
    assert "CHAPTER" in texts[1] or "ONE" in texts[1]
    assert "PARIS" in texts[2] or "1927" in texts[2]

    for candidate in result.candidates:
        assert 0 < candidate.start_us < candidate.end_us <= result.media.duration_us + 500_000
        assert candidate.ocr_confidence > 0.5
        assert candidate.detection_score > 0

    assert format_timecode(result.candidates[0].start_us).startswith("00:00:01")


def test_missing_file_has_a_stable_error() -> None:
    from silent_cinema.media.process import MediaProcessError

    with pytest.raises(MediaProcessError) as caught:
        probe_media(Path("/nonexistent/film.mp4"))

    assert caught.value.code == "media_missing"
