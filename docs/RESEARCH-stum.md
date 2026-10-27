# Research: `stum` intertitle detection and OCR

Research date: **2026-10-27**. Sources: the official repository, its `README`,
`pyproject.toml`, `LICENSE`, and PyPI metadata.

## 1. What it is

`stum` is a Python tool for detecting and extracting text from intertitles in
silent films. It was developed for Swedish newsreels in the **Modern Times
1936** research project at Lund University. It extracts frames, groups them by
image similarity, filters candidate sequences by contours and OCR, merges
similar consecutive OCR output, and writes an SRT file using frame numbers.

- Repository: <https://github.com/Modern36/stum>
- PyPI: `stum` **0.2.0**
- Python requirement: `>=3.10`
- Default branch: `main`
- Last push observed: **2025-06-05**
- Stars observed: **1**; forks: 0
- Development status classifier: Beta
- Test data: a **private** submodule; not publicly reproducible

## 2. Dependencies and external requirements

Runtime dependencies (`pyproject.toml`):

```text
python-ffmpeg>=2.0.12
pytesseract>=0.3.13
opencv-contrib-python>=4.11.0.86
jiwer>=3.1.0
tqdm>=4.67.1
```

External requirements:

- FFmpeg binary.
- Tesseract binary.
- Swedish Tesseract model (`swe.traineddata`) for its tested use case.
- EAST text-detection model (`frozen_east_text_detection.pb`) downloaded
  separately and placed in `./models`.

The CLI:

```text
stum -i input.mpg
stum -i input_dir/
```

It writes one `.srt` per input video. `-d` saves intertitle frames; `-s` skips
existing SRTs.

## 3. Licence — the decisive constraint

**CC-BY-NC 4.0** (Attribution-NonCommercial 4.0 International).

- Not an OSI-approved open-source licence.
- Prohibits use "primarily intended for or directed towards commercial
  advantage or monetary compensation."
- Requires attribution and indication of modifications.
- The repository's GitHub licence detection reports `NOASSERTION`, but the
  `LICENSE` file and `pyproject.toml` both state CC-BY-NC-4.0.

Consequences:

- We may not vendor, copy, or redistribute `stum` code in an MIT project.
- We may not bundle its models or private test data.
- We may not import it as an in-process library without making the distributed
  combination subject to NC terms.
- An optional, separately installed CLI adapter keeps our code MIT, but
  **enabling it is a non-commercial use** and must be disclosed.

## 4. Quality and reliability observations

- Targeted at Swedish newsreels; accuracy on Indian silent-film intertitles is
  unknown.
- The README itself notes challenges: many digitised newsreels contain only a
  single frame per intertitle, and some intertitles are mirrored vertically.
- Its accuracy example shows raw Tesseract output with visible errors even on
  its own sample.
- Private test data means we cannot independently reproduce its benchmark.
- Single maintainer, low activity; API/CLI drift risk is real.
- Python 3.13 compatibility is declared but not verified by us.

## 5. Decision

Adopt **Option 2: optional external CLI adapter**, recorded in ADR-0003.

- Default detector: our own native OpenCV/Tesseract implementation.
- `StumCliDetector`: opt-in, disabled by default (`STUM_ENABLED=false`).
- No `stum` code, models, or data in this repository.
- The adapter:
  1. verifies the binary and version,
  2. creates a per-job working directory,
  3. invokes `[stum_bin, "-i", input_path]` with `shell=False`, a timeout, and
     a minimal environment,
  4. reads the SRT it emits,
  5. parses and validates the SRT with **our** parser,
  6. maps failures to typed error codes,
  7. deletes the working directory in `finally`.
- Contract tests use a fake `stum` executable; a real run is a documented
  manual check.
- The UI shows a persistent CC-BY-NC notice when the adapter is enabled.
- Installation instructions live in `DEPLOYMENT.md`.

## 6. Integration risks and mitigations

| Risk | Mitigation |
|---|---|
| `stum` may not install cleanly | Install with `pipx` in an isolated environment; never import in-process; `make doctor` reports status |
| Output format drift | Parse strictly; reject unknown/malformed SRT; pin a tested version; contract tests |
| CLI argument drift | Invoke only documented `-i`; verify `--help` output in a manual check |
| Non-Swedish accuracy | No accuracy claim; per-detector labelling; benchmark on our own fixture first |
| Model downloads | Operator-installed; never committed; documented |
| Licence violation | Disabled by default; no redistribution; explicit notice; attribution |
| Python 3.13 incompatibility | Declared `>=3.10`; verify at install time before enabling in CI |

## 7. Verification status

| Claim | Status |
|---|---|
| Repository and licence | `[VERIFIED]` 2026-10-27 |
| PyPI 0.2.0 metadata | `[VERIFIED]` 2026-10-27 |
| Installs on Python 3.13 | `[UNVERIFIED]` |
| Runs on this machine | `[BLOCKED]` — FFmpeg/Tesseract not installed |
| Accuracy on Indian films | `[UNVERIFIED]` — no corpus |
| SRT output shape | `[UNVERIFIED]` — to be tested in M4 |
