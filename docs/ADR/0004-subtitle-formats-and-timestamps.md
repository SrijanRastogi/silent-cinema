# ADR-0004 — Subtitle formats, timestamps, and export flow

- **Status:** Accepted (M0)
- **Date:** 2026-10-27

## Context

Subtitles must be accurately timed and encoded. Frame counts and floating-point
seconds introduce drift, especially with variable frame rate. The suggested API
had a direct `GET .../export?format=srt` endpoint, which makes it hard to prove
that a downloadable file was validated.

## Decision

1. Store all media positions as **integer microseconds** (`bigint`, `*_us`).
   API fields use the same unit.
2. Derive positions from `pts × time_base` using the exact rational timebase
   from ffprobe. Never compute from `frame / rounded_fps`.
3. Convert to milliseconds only at serialization, using half-up rounding, with
   boundary tests (`999499 µs`, `999500 µs`).
4. **SRT is the primary format; WebVTT is secondary.**
5. Serializers implement:
   - sequence numbering from 1,
   - `HH:MM:SS,mmm` for SRT and `HH:MM:SS.mmm` for VTT,
   - UTF-8 output without BOM,
   - text normalization that preserves Unicode and converts unsafe newlines,
   - rejection of empty tracks, non-positive durations, and overlaps.
6. Export is a two-step flow:
   - `POST /subtitle-tracks/{id}/exports` produces and validates an artifact,
   - `GET /exports/{id}/download` serves only `valid` artifacts.
7. Every artifact records `sha256`, `entry_count`, `byte_size`, and
   `validation_status`.
8. After writing, the file is re-parsed and validated before the artifact is
   marked valid. A job reaches `completed` only after a valid artifact exists.
9. Subtitles are never burned into or re-encoded with the source video.

## Rationale

- Integer microseconds avoid float drift and preserve frame accuracy.
- Rational timebase is the only correct way to handle VFR.
- Validating before download prevents shipping a corrupt file.
- Create-then-download gives an auditable artifact record.

## Consequences

- The API deviates from the suggested direct-download endpoint; documented in
  `API.md` §3.6.
- The frontend must display and validate `*_us`, not seconds.
- SRT output is limited to millisecond precision by the format itself; this is
  stated in the UI when a source is more precise.

## Verification

No serializer exists yet. Round-trip tests with VLC and a common editor are
required in M6 before claiming compatibility. `[PLANNED]`
