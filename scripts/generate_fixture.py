#!/usr/bin/env python3
"""Generate the deterministic synthetic silent-film fixture used by media tests.

The fixture is 18 seconds of 640x480 video at 10 fps with three intertitle
cards separated by black leader. It contains no third-party footage.

Usage:
    python scripts/generate_fixture.py [--output PATH]

FFmpeg must be on PATH (or set ``FFMPEG_BIN``). The font is discovered from
common system paths or ``FIXTURE_FONT``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "fixtures" / "synthetic-intertitles.mp4"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

CARDS = [
    (1.0, 4.0, "THE LOST REEL", "A silent film fragment"),
    (7.0, 10.5, "CHAPTER ONE", "The Empty Theatre"),
    (13.0, 16.5, "PARIS, 1927", "Reel two is missing"),
]


def find_font() -> str:
    override = os.environ.get("FIXTURE_FONT")
    if override:
        return override
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit(
        "No usable font found. Set FIXTURE_FONT to a .ttf path before generating the fixture."
    )


def build_filter(font: str) -> str:
    parts: list[str] = []
    for start, end, title, subtitle in CARDS:
        window = f"between(t\\,{start}\\,{end})"
        parts.append(
            "drawtext="
            f"fontfile={font}:text='{title}':fontcolor=0xF2EAD9:fontsize=44:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-28:enable='{window}'"
        )
        parts.append(
            "drawtext="
            f"fontfile={font}:text='{subtitle}':fontcolor=0xCFC5B4:fontsize=24:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+34:enable='{window}'"
        )
    return ",".join(parts)


def generate(output: Path = DEFAULT_OUTPUT) -> Path:
    """Render the fixture and return its path. Deterministic for a given FFmpeg."""
    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = os.environ.get("FFMPEG_BIN", "ffmpeg")
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x0B0B0B:s=640x480:r=10:d=18",
        "-vf",
        build_filter(find_font()),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise SystemExit(f"FFmpeg failed:\n{result.stderr.strip()}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    path = generate(args.output)
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
