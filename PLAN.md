# PLAN.md — Implementation Roadmap

This is the authoritative roadmap. `docs/STATUS.md` records live progress.
`AGENTS.md` defines how work must be performed.

## Current state

- **Current milestone:** M0 — Foundation (documentation delivered, pending review)
- **Application code:** none
- **Database:** not created
- **Tests:** none runnable yet
- **Next approved action:** review M0, then M1 scaffold

> M0 does not implement the application. Any statement implying otherwise is
> false.

## Product outcome

A user can upload a silent film, run intertitle detection and OCR, review and
correct the results with accurate timestamps, and export valid SRT (primary)
and WebVTT (secondary) subtitles for use in VLC and common editors. English is
the first OCR target; the data model, editor, and exporters must remain
Unicode-safe and language-agnostic. No OCR language is claimed as supported
until it has been tested with representative samples.

## Milestones

| ID | Name | Depends on | Status |
|---|---|---|---|
| M0 | Foundation: docs, decisions, quality gates | — | Documentation delivered; awaiting review |
| M1 | Scaffold, database, CI | M0 | Planned |
| M2 | Upload, storage, dashboard shell | M1 | Planned |
| M3 | Worker, queue, media probing | M1, M2 | Planned |
| M4 | Intertitle detection and OCR | M3 | Planned |
| M5 | Review editor | M4 | Planned |
| M6 | SRT/WebVTT export and preview | M5 | Planned |
| M7 | Integration, security, deployment | M6 | Planned |

No milestone starts before the previous one passes its acceptance criteria,
unless a documented dependency justifies reordering and the human owner
approves it.

---

## M0 — Foundation

### Scope

Documentation, decisions, quality gates, skill definitions, repository
initialisation. No application code, no dependencies installed, no shadcn
components, no database.

### Deliverables

- Root docs: `README.md`, `PLAN.md`, `AGENTS.md`, `ARCHITECTURE.md`, `API.md`,
  `DATABASE.md`, `TESTING.md`, `DEPLOYMENT.md`, `SECURITY.md`,
  `CONTRIBUTING.md`, `CHANGELOG.md`, `BACKLOG.md`, `THIRD_PARTY_NOTICES.md`,
  `LICENSE`.
- State docs: `docs/STATUS.md`, `docs/DECISIONS.md`, `docs/REVIEW_LOG.md`,
  `docs/QUALITY_GATES.md`, `docs/RESEARCH-stum.md`, `docs/UI.md`.
- ADRs 0001–0007.
- Project skills in `.opencode/skills/`.
- `opencode.jsonc`, `.gitignore`, `.editorconfig`.

### Acceptance criteria

- [x] Repository initialised on `main`.
- [x] Required documents exist and are mutually consistent.
- [x] `stum` research records licence, dependencies, risks, and decision.
- [x] Stack decisions recorded with versions and verification status.
- [x] Database and API designs documented, including relationships and
      constraints.
- [x] Quality gates and evidence rules defined.
- [x] M1 acceptance criteria defined.
- [x] No document claims unimplemented functionality.
- [ ] Conductor/human review recorded.

### Validation

```bash
git status --short
find . -maxdepth 3 -name '*.md' | sort
# Manual consistency review: status labels, links, versions.
```

No executable application checks exist in M0.

---

## M1 — Scaffold, database, CI

Status: **implemented, awaiting review.** See `docs/STATUS.md` for commands and
results.

### Scope

A runnable skeleton with a real database connection, migrations, API health
endpoint, frontend shell, and CI. No upload, no worker, no OCR.

### Tasks

1. Create `pyproject.toml` with Python 3.13, pinned backend dependencies, Ruff,
   MyPy, Pytest configuration.
2. Create `apps/api` package with settings (Pydantic), app factory, `/api/v1`
   router, health and readiness endpoints, structured error envelope.
3. Create SQLAlchemy 2.x base/session, naming conventions, and engine setup.
4. Create the initial Alembic migration for `media_assets` and
   `processing_jobs` only (schema documented in `DATABASE.md`).
5. Create `docker-compose.yml` with PostgreSQL 18, API, and worker placeholder.
6. Create `apps/web` with Vite + React 19 + TypeScript 5.9 strict + Tailwind 4,
   shadcn/ui initialised, routing shell, and an honest empty dashboard.
7. Add `Makefile` with `bootstrap`, `doctor`, `check`, `migrate`, `migrate-down`,
   `dev`, `test`, `test-integration`, `build`, `docs-check`.
8. Add `.github/workflows/ci.yml` with backend, frontend, and integration
   checks. Pin actions by commit SHA.
9. Add `tests/` with health, settings, migration, and dashboard-shell tests.
10. Add a fixture generator that creates a tiny synthetic video with FFmpeg
    (not committed).

### Acceptance criteria

1. `uv sync --frozen` succeeds on Python 3.13.
2. `ruff check`, `ruff format --check`, `mypy`, and `pytest` pass.
3. `alembic upgrade head` and `alembic downgrade base` pass against PostgreSQL
   18.
4. `docker compose config` and `docker compose up -d db` succeed.
5. `GET /api/v1/health` returns 200 with a real database check; `/api/v1/health/ready`
   behaves correctly when the database is unavailable.
6. OpenAPI is served at `/api/v1/openapi.json` and matches `API.md` for the
   endpoints implemented in M1.
7. `npm ci`, ESLint, `tsc --noEmit`, `vitest run`, and `vite build` pass.
8. Dashboard shell renders with real empty states and no invented metrics.
9. `make doctor` reports versions and missing tools accurately.
10. CI workflow is authored; it is **not** claimed as executed until a remote
    repository exists.

### Validation commands

```bash
make doctor
uv sync --frozen
make check
make migrate
make migrate-down && make migrate
docker compose config
docker compose up -d db
npm --prefix apps/web ci
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build
```

---

## M2 — Upload, storage, dashboard shell

### Scope

Secure upload and metadata persistence; real dashboard entry point. No
processing yet.

### Tasks

1. Storage abstraction with local adapter; roots for `uploads/`, `work/`,
   `exports/`.
2. `POST /api/v1/media` multipart upload with size limit, extension allowlist,
   streamed write, SHA-256, and ffprobe validation.
3. `GET /api/v1/media/{id}` and paginated `GET /api/v1/media`.
4. Media deletion policy and orphan cleanup script (explicit, not automatic).
5. Upload page with drag-and-drop, real progress, and actionable errors.
6. Dashboard lists real media; failed probe states shown honestly.
7. Tests: oversized, empty, wrong extension, path traversal, malformed media,
   duplicate SHA-256, storage cleanup.

### Acceptance criteria

- Invalid inputs are rejected with stable error codes and no leftover files.
- Valid uploads persist metadata and survive restart.
- No client filename is used as a storage path.
- Dashboard shows only real data.

---

## M3 — Worker, queue, media probing

### Scope

Asynchronous processing foundation and media probing. No detection/OCR yet.

### Tasks

1. DB-backed queue with claim/lease semantics (`FOR UPDATE SKIP LOCKED`),
   attempt counting, and stale-lease recovery.
2. Worker entrypoint with graceful shutdown and cancellation checks.
3. Job creation endpoint with `Idempotency-Key` and partial unique index for
   active jobs.
4. Job status endpoint and cancel endpoint with documented transitions.
5. Probe stage: duration, dimensions, frame rate, timebase, stream inventory.
6. Structured logging with job/media correlation; no secrets or absolute paths
   in responses.
7. Tests: concurrent claims, duplicate job creation, cancellation, stale
   recovery, probe failure, temp cleanup.

### Acceptance criteria

- Two workers cannot claim the same job.
- Invalid transitions are rejected.
- Cancellation stops work at safe checkpoints and cleans temp files.
- Job status matches worker state after restart.

---

## M4 — Intertitle detection and OCR

Status: **core pipeline implemented early at the owner's request; persistence,
HTTP API, review UI, and `stum` adapter remain.** The native detector, PTS-based
frame sampling, Tesseract adapter, CLI, fixture, and tests exist.

### Scope

Native detector (default) and optional external `stum` adapter; OCR via
Tesseract. English only until other languages are tested.

### Tasks

1. `IntertitleDetector` interface with typed input/output and error codes.
2. Native detector: frame sampling, shot grouping, text-region heuristics,
   candidate interval merging. Documented parameters.
3. Crop/upscale/binarize pipeline; OCR with Tesseract TSV confidence.
4. Optional `StumCliDetector`: disabled by default, requires external `stum`,
   runs with argv arrays, parses and validates generated SRT, maps errors.
5. Persist intertitles and create a `SubtitleTrack` with `SubtitleEntry` rows.
6. Detection fixture: synthetic video with known text cards; real-video test
   kept separate and optional.
7. Tests: detector interface, interval merge, timebase mapping, adapter parsing
   with a fake `stum` executable, OCR failure, unsupported language handling.

### Acceptance criteria

- Detection runs on the validated synthetic fixture and produces plausible
  intervals.
- Every result carries a timestamp derived from `pts × time_base`.
- `stum` cannot be enabled without an explicit setting and a clear UI notice.
- No accuracy claim is made beyond the tested fixture.

---

## M5 — Review editor

### Scope

Human correction workflow.

### Tasks

1. Video preview with subtitle overlay and seek-to-entry.
2. Entry list with edit, add, delete, reorder; overlap and ordering validation.
3. Distinguish machine-generated vs reviewed content.
4. Optimistic-free, explicit save states; conflict handling on stale updates.
5. Keyboard shortcuts and accessible controls.
6. Tests: editing, validation, reorder, add/delete, stale update, Unicode,
   undo/redo if implemented.

### Acceptance criteria

- A user can correct text and timings without corrupting other entries.
- Invalid/overlapping timings are blocked with a clear message.
- Reviewed state is visible and persisted.

---

## M6 — SRT/WebVTT export and preview

### Scope

Validated export and in-browser synchronization preview.

### Tasks

1. Timecode module: microseconds ↔ SRT/VTT, rounding policy, validation.
2. SRT and WebVTT serializers with Unicode preservation and line-break rules.
3. Export artifact creation, checksum, entry count, and validation before job
   completion.
4. Download endpoints with correct content type/disposition and safe filenames.
5. Export page: preview, validation errors, downloads.
6. Tests: serialization golden files, round-trip parsing, Unicode/emoji/RTL,
   ordering, overlaps, empty tracks, millisecond rounding, large tracks.

### Acceptance criteria

- SRT and VTT load in VLC and a common editor.
- UTF-8 content is preserved without corruption.
- Invalid tracks cannot be exported.
- No burn-in or re-encoding of source video.

---

## M7 — Integration, security, deployment

### Scope

Hardening and reproducible delivery.

### Tasks

1. Playwright E2E for the primary workflow plus failure paths.
2. Security review: uploads, subprocess isolation, path containment, headers,
   error leakage, dependency audit, secret scanning.
3. Data retention and cleanup verification.
4. Docker images for API and worker; production compose profile.
5. Deployment and recovery documentation validated from a clean state.
6. Performance baseline on the smallest supported machine; no invented numbers.

### Acceptance criteria

- Full workflow passes E2E against real services.
- Security checks pass or exceptions are documented and approved.
- Clean-machine deployment instructions work.
- Documentation reflects actual behaviour and limitations.

---

## Dependencies

```text
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7
                └──────→ M4 (requires probe + storage)
```

Hard dependencies:

- M1 before any code.
- M2 before M3 (media records and files).
- M3 before M4 (job runner and probe metadata).
- M4 before M5 (intertitles to edit).
- M5 before M6 (tracks to export).
- M7 after all.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| No Docker/FFmpeg/Tesseract/Postgres on dev machine | Blocks M1/M3/M4 verification | Install via apt with sudo; `make doctor` reports gaps; Docker Compose for parity |
| `stum` is CC-BY-NC | Cannot bundle or redistribute | External opt-in CLI adapter only; no code copying; documented in UI and notices |
| OCR accuracy unproven | False product claims | Synthetic fixture first; real-film evaluation separate; explicit limitations |
| Variable frame rate | Wrong subtitle timings | Always use PTS × timebase; VFR fixture in M4 |
| 11 GB free disk | Fixture/build failures | Small synthetic fixtures; clean work dirs; document space needs |
| No auth | Local exposure | Bind to loopback; document single-user boundary; no public deployment claim |
| CI not executable without remote | Unverified gates | Author CI in M1; run locally; record remote status honestly |

## Validation policy

Every milestone closes with:

1. Acceptance criteria demonstrated.
2. `make check` output recorded in `docs/STATUS.md`.
3. Migration up/down evidence when schema changed.
4. Documentation updated and consistent.
5. Review entry in `docs/REVIEW_LOG.md` or an explicit "not reviewed" note.

## Scope fence

Out of scope for the initial release: machine translation, TTS/narration,
dubbing, character identification, lip sync, public archives, social features,
payments, multi-tenancy, custom model training, and any feature that does not
serve the core workflow. See `BACKLOG.md`.
