# ADR-0003 — Intertitle detection and OCR

- **Status:** Accepted (M0)
- **Date:** 2026-10-27

## Context

Intertitles are embedded in the video and must be located and transcribed with
accurate timestamps. `stum` is an existing implementation but is licensed
CC-BY-NC 4.0 and targets Swedish newsreels. OCR libraries alone do not provide
reliable intertitle detection.

## Decision

1. Define an `IntertitleDetector` interface with typed input/output and error
   codes.
2. Implement a **native detector by default**:
   - sample frames at a configurable rate,
   - group stable frames into candidate shots,
   - score regions for text-like edges/contrast/connected components,
   - merge consecutive candidates,
   - crop, upscale, binarize, and OCR with Tesseract,
   - record Tesseract confidence where available.
3. Define an `OcrEngine` interface; Tesseract is the first implementation.
4. Provide an **optional `StumCliDetector`**:
   - disabled by default (`STUM_ENABLED=false`),
   - requires an externally installed `stum` binary,
   - invokes it with an argument array and timeout in a per-job temp directory,
   - parses the emitted SRT with **our** parser and validates timestamps,
   - maps failures to typed errors,
   - never imports `stum` in-process.
5. Do not copy, vendor, or redistribute `stum` code, models, or data.
6. Default OCR language is English (`eng`). Other installed languages may be
   selected, but support is only claimed after representative testing. The data
   model, editor, and exporters are Unicode-safe and language-agnostic.
7. No accuracy claim is made from a single sample or from `stum`'s README.

## Rationale

- A native default keeps the project MIT-licensed and usable without the NC
  restriction.
- An adapter preserves the option to use `stum` for users who accept its terms.
- Hiding engine differences behind interfaces prevents the pipeline from
  depending on a specific CLI or library.
- The NC restriction is a legal boundary, not a technical preference.

## Consequences

- Two detector implementations must be maintained; the adapter is intentionally
  small.
- Native detector quality must be evaluated on real material before any claim.
- `stum` installation is an operator responsibility, documented in
  `DEPLOYMENT.md` and `docs/RESEARCH-stum.md`.
- The UI must disclose when a non-commercial engine is active.

## Risks

- OCR accuracy on historical prints (scratches, flicker, low contrast) is
  unknown.
- Mirrored or single-frame intertitles may need special handling.
- Variable frame rate must be tested explicitly.
