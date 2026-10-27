# Changelog

All notable changes are recorded here. The project follows a milestone-based
history; versions are assigned at release time.

## [Unreleased]

### Added — M1 scaffold, database, and CI

- Added pinned Python 3.13 backend dependencies, Ruff, MyPy, and Pytest.
- Added the FastAPI app factory, typed settings, `/api/v1` router, liveness and
  PostgreSQL readiness checks, request IDs, and the error envelope.
- Added SQLAlchemy models and the initial Alembic migration for
  `media_assets` and `processing_jobs`.
- Added Docker Compose for PostgreSQL 18 and the API, a parity Dockerfile, and
  an explicit worker placeholder that refuses to pretend it processes jobs.
- Added the React 19/Vite 8/TypeScript/Tailwind frontend shell with an honest
  empty dashboard, system status page, theme toggle, 404 page, and real tests.
- Added `Makefile` targets, documentation validation, fixture generation, and
  a GitHub Actions CI workflow with pinned action SHAs.

### Added — native intertitle detection and OCR (M4 core, early)

- Added FFmpeg probing, PTS-based frame sampling, OpenCV candidate detection,
  interval grouping, and Tesseract OCR behind interfaces.
- Added `scripts/detect_intertitles.py` for local verification.
- Added a generated 18-second synthetic fixture and unit/media tests. The
  pipeline found the three known cards with exact intervals on that fixture.

### Notes

- The pipeline is not yet reachable from the web UI and does not persist
  results; those are M2/M4/M5 work.
- No Docker container or CI workflow has been executed in this environment.
- No application code has been committed; the tree is untracked pending review.

### Added — M0 Foundation

- Initialised the repository on `main`.
- Added the engineering operating contract (`AGENTS.md`) with evidence,
  scope-control, security, and completion rules.
- Added the milestone roadmap (`PLAN.md`) with acceptance criteria and
  validation commands.
- Added architecture, API, database, testing, deployment, security, UI, and
  quality-gate documents.
- Added Architecture Decision Records 0001–0007.
- Added project skills for context loading, feature gating, UI work, backend
  contracts, media/subtitles, and evidence reporting.
- Added `stum` research and the optional CC-BY-NC adapter decision.
- Added third-party notices and the MIT licence.

### M0 notes

- No application code, database, or CI pipeline exists yet.
- Nothing in this release has been deployed or benchmarked.
