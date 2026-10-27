---
name: Media and Subtitles
description: Safely implement FFmpeg/ffprobe probing and frame extraction, intertitle detection, Tesseract or optional stum OCR, timestamp math, and validated SRT/WebVTT serialization.
---

# Media and Subtitles

Use for `apps/api/media`, `detection`, `ocr`, `subtitles`, worker media stages,
and export tests.

## Media safety

- `subprocess` with `list[str]`, `shell=False`, no string interpolation.
- Resolve binaries from configuration; prefer absolute paths.
- Per-process timeout; kill the process group on timeout/cancel.
- Run inside the job's `work/` directory, never a user-controlled cwd.
- Minimise the environment; pass no secrets.
- Clean temp files in `finally` and sweep orphans at worker startup.
- Treat every upload as hostile: ffprobe must confirm a real video stream.

## Probing

- Use ffprobe JSON output.
- Record duration, width, height, exact rational frame rate, and timebase.
- Convert frames with `pts × time_base`; never `frame / rounded_fps`.
- Reject zero/negative durations and missing video streams.

## Detection and OCR

- Implement behind `IntertitleDetector` and `OcrEngine` interfaces.
- The pipeline must not import Tesseract or `stum` directly.
- Default detector is native; `stum` is opt-in and disabled by default.
- Record OCR confidence when the engine supplies it; never fabricate it.
- An empty OCR result must be surfaced for review, not silently dropped.
- Do not claim language or accuracy support beyond tested samples.

## `stum` adapter

- Invoke `[stum_bin, "-i", path]` with a timeout in a per-job temp dir.
- Parse the emitted SRT with **our** parser; validate timestamps and ordering.
- Map non-zero exits and malformed output to typed errors.
- Never import `stum`; never vendor its code, models, or data.
- Show the CC-BY-NC notice when enabled.

## Subtitles

- Store and exchange microseconds.
- SRT: `HH:MM:SS,mmm`, sequence from 1, UTF-8, no BOM.
- VTT: `WEBVTT` header, `HH:MM:SS.mmm`, no BOM.
- Round to milliseconds half-up at serialization; test boundaries.
- Preserve Unicode; normalize only what would break the format.
- Reject empty tracks, `end <= start`, overlaps, and non-finite values.
- Re-parse generated output before marking it valid.
- Never burn subtitles into the video.

## Tests

- Golden-file serializer tests.
- Round-trip parse of generated SRT/VTT.
- Unicode, RTL, emoji, multiline, long cue, rounding boundaries.
- VFR fixture with known PTS values.
- Adapter contract test with a fake `stum` executable.
- Optional real-media test behind an explicit marker.
