# ADR-0001 — Approved technology stack

- **Status:** Accepted (M0)
- **Date:** 2026-10-27
- **Deciders:** Human owner, OpenCode

## Context

The project needs a maintainable full-stack foundation for media processing,
a review UI, and reliable export. The proposed stack must support Python
media/OCR libraries and a modern React frontend on a modest Linux machine.

## Decision

| Layer | Choice |
|---|---|
| Backend language | Python **3.13** (system package `python3.13`) |
| API | FastAPI, Pydantic v2, Uvicorn |
| ORM / migrations | SQLAlchemy 2.x, Alembic, psycopg 3 |
| Database | PostgreSQL 18 |
| Queue | PostgreSQL table + `FOR UPDATE SKIP LOCKED` |
| Media | FFmpeg 8 / ffprobe, OpenCV 5 headless |
| OCR | Tesseract 5.5 via pytesseract |
| Frontend | React 19, Vite 8, TypeScript **5.9.3** strict |
| Styling | Tailwind CSS 4 |
| Components | shadcn/ui + selected Watermelon UI registry blocks |
| Routing / state | React Router 7, TanStack Query 5 |
| Forms | React Hook Form 7, Zod 4 |
| Tests | Pytest, Vitest, React Testing Library, Playwright |
| Package manager | npm 11 with committed `package-lock.json`; uv for Python |

## Rationale

- Python 3.13 is available in Ubuntu 26.04 and has broad wheel support for the
  media/OCR stack. The system default 3.14 is too new to assume ecosystem
  readiness; no compatibility claim is made for it.
- TypeScript 7 exists (native compiler rewrite) but ecosystem tooling
  (ESLint, Vite plugins, shadcn generators) is not yet proven with it. Pin
  5.9.3 and revisit deliberately.
- PostgreSQL provides the durability, constraints, and locking needed for a
  reliable job queue without adding Redis.
- npm avoids introducing pnpm before it is needed.
- Vite 8 requires Node ≥20.19/22.12; Node 24 satisfies this.

## Consequences

- Python 3.13 must be installed explicitly.
- Vite 8 + shadcn CLI compatibility must be verified in M1.
- Every dependency is pinned and licence-checked.
- Changing a major version or adding a new runtime service requires a new ADR.

## Verification status

Versions were confirmed against PyPI/npm/apt metadata on 2026-10-27. They have
**not** been installed or run yet. `[VERIFIED: existence]`, `[UNVERIFIED:
compatibility]`.
