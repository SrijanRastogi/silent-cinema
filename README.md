# Silent Cinema in Your Language

Extract intertitles from silent films, correct the OCR, and export properly
timed subtitles.

> **Status: M1 scaffold plus the native detection/OCR core.** The backend,
> database migrations, frontend shell, CI workflow, and a verified
> FFmpeg/OpenCV/Tesseract pipeline exist. Upload, persistence, the review
> editor, and export are still planned, so the web UI cannot yet run the
> pipeline. Nothing has been deployed, benchmarked, or reviewed by the human
> owner.

## The problem

Silent films carry dialogue and narration in intertitle cards embedded in the
video. Finding those cards and retyping them into synchronized subtitles is slow
and error-prone. This project aims to make that workflow reviewable and
repeatable: detect candidate intertitles, OCR them, let a human correct the
result, and export valid subtitle files without touching the film.

## Target workflow

```text
Upload film → validate → probe → detect intertitles → OCR
    → review and correct → export SRT / WebVTT → preview and download
```

Planned capabilities:

- Upload a supported video with real validation and progress.
- Process asynchronously and show real job state.
- Detect intertitle intervals and OCR them with timestamps.
- Review, edit, add, delete, and reorder subtitle entries.
- Export UTF-8 SRT (primary) and WebVTT (secondary).
- Preview subtitles against the original video.
- Review job history, failures, and safe error messages.

Not in the initial release: translation, TTS/dubbing, character identification,
lip sync, public archives, social features, payments, multi-tenancy, or custom
model training.

## Architecture

A modular monolith with three processes:

```text
React SPA  →  FastAPI (/api/v1)  →  PostgreSQL
                     │
                     └── worker (same services) → filesystem
```

- PostgreSQL is both the system of record and the job queue
  (`FOR UPDATE SKIP LOCKED`), so no Redis is required.
- Media lives on the filesystem in managed `uploads/`, `work/`, and `exports/`
  roots; never in the database.
- FFmpeg/ffprobe, OpenCV, and Tesseract do the media work behind interfaces.
- `stum` is an optional external CLI adapter, disabled by default, with a
  non-commercial licence (see below).

See `ARCHITECTURE.md`, `docs/ADR/`, and `docs/UI.md`.

## Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 18 |
| Media | FFmpeg 8, OpenCV 5, Tesseract 5.5 |
| Frontend | React 19, Vite 8, TypeScript 5.9, Tailwind CSS 4 |
| Components | shadcn/ui, selected Watermelon UI registry blocks (MIT) |
| State / forms | TanStack Query 5, React Router 7, React Hook Form 7, Zod 4 |
| Tests | Pytest, Vitest, React Testing Library, Playwright |
| Quality | Ruff, MyPy, ESLint, Prettier, CI |

## Prerequisites

- Linux (Ubuntu 26.04 tested for package availability) or macOS for development.
- Python 3.13, Node 24, npm 11.
- PostgreSQL 18.
- FFmpeg 8 and Tesseract 5.5 with the desired language packs.
- Docker + Compose (optional, for parity).

Ubuntu packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  postgresql-18 python3.13 python3.13-venv \
  ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin \
  libpq-dev
```

## Local development (planned, M1)

These commands do not work yet. They are the contract the scaffold must fulfil.

```bash
cp .env.example .env
make doctor
make bootstrap
make migrate
make dev
```

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`

The worker is a separate process. If it is not running, jobs stay queued and the
UI must say so rather than pretending to process.

## Environment

Configuration is documented in `DEPLOYMENT.md` §3. Never commit `.env`.

Key variables: `DATABASE_URL`, `STORAGE_ROOT`, `MAX_UPLOAD_BYTES`,
`FFMPEG_BIN`, `FFPROBE_BIN`, `OCR_DEFAULT_LANGUAGE`, `STUM_ENABLED`.

## Tests (planned)

```bash
make check
make test
make test-integration
make e2e
```

No test suite exists yet. `TESTING.md` defines the strategy, fixtures, coverage
policy, and known gaps.

## Supported inputs and limitations

Intended:

- Common containers: MP4, MKV, MOV, AVI, MPEG, WebM.
- A video stream is required; audio-only files are rejected.
- English OCR first. Other Tesseract languages may be installed and selected,
  but **no language is claimed as supported until tested with representative
  samples**.
- UTF-8 subtitle output, including non-Latin scripts.
- SRT is primary; WebVTT secondary.

Known limitations:

- No accuracy benchmark on historical films yet.
- Variable frame rate is designed for but untested.
- Single-user, local-only; no authentication.
- Large films require significant temporary disk space.
- `stum` is not redistributed and is non-commercial.

## Documentation

| File | Purpose |
|---|---|
| `PLAN.md` | Milestones, acceptance criteria, validation |
| `AGENTS.md` | Binding rules for coding agents |
| `docs/QUALITY_GATES.md` | Pre/post feature gates and evidence rules |
| `ARCHITECTURE.md` | Components, pipeline, state machine, storage |
| `API.md` | Endpoint and error contract |
| `DATABASE.md` | Schema, constraints, indexes, retention |
| `TESTING.md` | Test layers, fixtures, coverage |
| `DEPLOYMENT.md` | Setup, env vars, migrations, operations |
| `SECURITY.md` | Boundaries and reporting |
| `docs/UI.md` | Design system and page requirements |
| `docs/STATUS.md` | Current milestone, blockers, evidence |
| `docs/DECISIONS.md` | Decision register |
| `docs/RESEARCH-stum.md` | `stum` evaluation |
| `THIRD_PARTY_NOTICES.md` | Licences and attribution |

## Licence

MIT (`LICENSE`). `stum` is **CC-BY-NC 4.0**, is not bundled, and is disabled by
default; enabling it makes that processing path non-commercial. See
`THIRD_PARTY_NOTICES.md` and ADR-0007.

## Contributing

Read `AGENTS.md` and `CONTRIBUTING.md` first. Work outside the current milestone
is deferred to `BACKLOG.md`.
