#!/usr/bin/env python3
"""Run native intertitle detection and Tesseract OCR on a local video.

This is the M4 core pipeline exposed for verification before upload and the
review UI exist. It never uploads anything and writes no files outside a
temporary directory.

Usage:
    python scripts/detect_intertitles.py FILM.mp4 [--lang eng] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from silent_cinema.media.pipeline import DetectionOptions, detect_intertitles  # noqa: E402
from silent_cinema.media.probe import MediaInfo  # noqa: E402
from silent_cinema.media.timecode import format_timecode  # noqa: E402


def serialise(media: MediaInfo, candidates: list[dict[str, object]]) -> dict[str, object]:
    return {
        "media": {
            "duration_us": media.duration_us,
            "width": media.width,
            "height": media.height,
            "frame_rate": f"{media.frame_rate_num}/{media.frame_rate_den}",
            "time_base": f"{media.time_base_num}/{media.time_base_den}",
        },
        "intertitles": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--lang", default=os.environ.get("OCR_DEFAULT_LANGUAGE", "eng"))
    parser.add_argument("--sample-fps", type=float, default=2.0)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args()

    try:
        result = detect_intertitles(
            args.video,
            options=DetectionOptions(sample_fps=args.sample_fps, ocr_language=args.lang),
            ffmpeg_bin=os.environ.get("FFMPEG_BIN", "ffmpeg"),
            ffprobe_bin=os.environ.get("FFPROBE_BIN", "ffprobe"),
        )
    except Exception as error:  # CLI boundary: report the code, never a traceback
        code = getattr(error, "code", "detection_failed")
        message = getattr(error, "message", str(error))
        print(f"error [{code}]: {message}", file=sys.stderr)
        return 1

    payload = [
        {
            "start_us": candidate.start_us,
            "end_us": candidate.end_us,
            "start": format_timecode(candidate.start_us),
            "end": format_timecode(candidate.end_us),
            "text": candidate.text,
            "ocr_confidence": candidate.ocr_confidence,
            "detection_score": candidate.detection_score,
            "frame_timestamp_us": candidate.frame_timestamp_us,
        }
        for candidate in result.candidates
    ]

    if args.json:
        print(json.dumps(serialise(result.media, payload), indent=2, ensure_ascii=False))
        return 0

    print(
        f"{args.video.name}: {format_timecode(result.media.duration_us)} "
        f"{result.media.width}x{result.media.height}, "
        f"{result.sampled_frames} sampled frames, {len(payload)} candidate(s)"
    )
    for index, candidate in enumerate(payload, start=1):
        confidence = float(candidate["ocr_confidence"])  # type: ignore[arg-type]
        print(
            f"{index:02d}  {candidate['start']} → {candidate['end']}  "
            f"score={candidate['detection_score']} ocr={confidence:.2f}"
        )
        text = str(candidate["text"]).replace("\n", " / ")
        print(f"    {text or '(no text recognised; needs review)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
