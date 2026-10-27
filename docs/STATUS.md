# STATUS.md

Updated: 2026-10-27

## Current milestone

**M1 — Scaffold, database, CI.** Implementation is complete and awaiting
human/conductor review. The M4 detection/OCR core pipeline was also
implemented early at the human owner's explicit request; its persistence, API,
and review UI remain planned.

## Active task

None. M1 is closed pending review. No M2 work has started.

## Completed in M1

- [x] `pyproject.toml` with Python 3.13, pinned backend dependencies, Ruff,
      MyPy, and Pytest configuration.
- [x] FastAPI app factory, typed settings, `/api/v1` router, liveness and
      readiness endpoints, request-id middleware, structured error envelope.
- [x] SQLAlchemy 2 engine/session/base with naming conventions.
- [x] Alembic initial migration for `media_assets` and `processing_jobs`.
- [x] `docker-compose.yml` (PostgreSQL 18, API, worker placeholder),
      `docker/api.Dockerfile`, and the worker refusal placeholder.
- [x] `apps/web` with Vite 8, React 19, TypeScript 5.9 strict, Tailwind 4,
      shadcn/Radix primitives, routing shell, honest empty dashboard, system
      status page, and 404 page.
- [x] `Makefile` targets and `scripts/check_docs.py`.
- [x] `.github/workflows/ci.yml` with pinned action commit SHAs.
- [x] Real frontend tests for status, errors, theme, routing, and API client.

## Completed early from M4 (explicit human request)

- [x] `IntertitleDetector` boundary and OpenCV heuristic detector.
- [x] FFmpeg frame sampling with timestamps read from `showinfo` PTS.
- [x] Tesseract OCR adapter with preprocessing, word confidences, and typed
      errors.
- [x] Interval grouping, best-frame selection, and OCR pipeline.
- [x] Synthetic fixture generator and `scripts/detect_intertitles.py` CLI.
- [x] Unit, media, and error-path tests.

Not yet implemented from M4: database persistence of intertitles/tracks,
HTTP endpoints, review UI, `StumCliDetector`, and shot-boundary grouping.

## Latest verification

| Check | Command | Result |
|---|---|---|
| Backend lint | `uv run ruff check .` | `[VERIFIED]` All checks passed |
| Backend format | `uv run ruff format --check .` | `[VERIFIED]` 71 files already formatted |
| Backend types | `uv run mypy` | `[VERIFIED]` Success, 28 source files |
| Backend unit | `uv run pytest -m "not integration and not media"` | `[VERIFIED]` 31 passed, 13 deselected |
| Backend integration | `uv run pytest -m integration` | `[VERIFIED]` 10 passed, 34 deselected |
| Media pipeline | `uv run pytest -m media` | `[VERIFIED]` 3 passed, 41 deselected |
| Migrations | `uv run alembic current` / `check` | `[VERIFIED]` `5696bce13c07 (head)`, no new operations |
| Frontend lint | `npm run lint` | `[VERIFIED]` exit 0, no warnings |
| Frontend format | `npm run format:check` | `[VERIFIED]` all files match Prettier |
| Frontend types | `npm run typecheck` | `[VERIFIED]` exit 0 |
| Frontend unit | `npm test` | `[VERIFIED]` 14 passed (4 files) |
| Frontend build | `npm run build` | `[VERIFIED]` built in 2.06 s; JS 352.04 kB (gzip 110.24 kB) |
| Docs gate | `uv run python scripts/check_docs.py` | `[VERIFIED]` 17 required docs, 33 Markdown files, skills and JSON valid |
| Compose schema | `docker compose config --quiet` | `[VERIFIED]` exit 0 |
| Container startup | `docker compose up -d db api` | `[BLOCKED]` session lacks Docker socket access until re-login |
| CI execution | GitHub Actions | `[BLOCKED]` no remote or authenticated `gh` CLI |
| E2E | Playwright | `[PLANNED]` browsers not installed; not required for M1 |

### Detection evidence

`uv run python scripts/detect_intertitles.py data/fixtures/synthetic-intertitles.mp4`:

```text
synthetic-intertitles.mp4: 00:00:18.000 640x480, 36 sampled frames, 3 candidate(s)
01  00:00:01.000 → 00:00:04.000  score=0.3167 ocr=0.86
    THE LOST REEL / A silent film fragment
02  00:00:07.000 → 00:00:10.500  score=0.307 ocr=0.96
    CHAPTER ONE / The Empty Theatre
03  00:00:13.000 → 00:00:16.500  score=0.2822 ocr=0.96
    PARIS, 1927 / Reel two is missing
```

This is the project-generated fixture only. No accuracy claim is made for real
film stock, other languages, or `stum`.

## Blockers

| Blocker | Impact | Owner |
|---|---|---|
| Docker socket inaccessible in this shell | Container startup/build cannot be verified until re-login | Human |
| No Git remote and no authenticated `gh` CLI | CI can only be authored; it has not run | Human |
| Playwright browsers not installed | E2E gate deferred until the workflow exists | Deferred |
| No Antigravity session | No conductor review is claimed | Human |

## Next approved action

1. Human review of M1 (structure, dependencies, API, UI, evidence above).
2. Approve M2 (upload, storage, real dashboard rows) before starting it.
3. Decide whether the early M4 pipeline is accepted as-is or re-sequenced.

No commit has been made. The working tree remains untracked pending approval.
