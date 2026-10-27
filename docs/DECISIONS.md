# DECISIONS.md

A decision register. ADRs hold the reasoning; this table is the index and
approval record.

| ID | Decision | Status | Approved by | Date |
|---|---|---|---|---|
| D-001 | Project is a modular monolith (API + worker + web) | Accepted | Human | 2026-10-27 |
| D-002 | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 18 | Accepted | Human | 2026-10-27 |
| D-003 | React 19, Vite 8, TypeScript 5.9, Tailwind 4, npm | Accepted | Human | 2026-10-27 |
| D-004 | Local filesystem storage, no cloud dependency in v1 | Accepted | Human | 2026-10-27 |
| D-005 | PostgreSQL-backed job queue, no Redis/Celery in v1 | Accepted | Human | 2026-10-27 |
| D-006 | Microsecond timestamps; PTS × timebase; SRT primary, VTT secondary | Accepted | Human | 2026-10-27 |
| D-007 | Native detector default; `stum` is an optional external CLI adapter | Accepted | Human | 2026-10-27 |
| D-008 | Repository is MIT; `stum` is not bundled and is CC-BY-NC | Accepted | Human | 2026-10-27 |
| D-009 | Single-user local deployment, no authentication in v1 | Accepted | Human | 2026-10-27 |
| D-010 | shadcn/ui + Watermelon UI registry (MIT), not the npm package | Accepted | Human | 2026-10-27 |
| D-011 | Create-then-download export flow instead of direct `?format=` download | Accepted | Human | 2026-10-27 |
| D-012 | Intertitles are immutable evidence; subtitle entries are editable | Accepted | Pending review | 2026-10-27 |

## ADR index

| ADR | Title |
|---|---|
| 0001 | Approved technology stack |
| 0002 | Storage and media processing |
| 0003 | Intertitle detection and OCR |
| 0004 | Subtitle formats, timestamps, and export flow |
| 0005 | Background processing and job state |
| 0006 | UI system: shadcn/ui and Watermelon UI |
| 0007 | Licensing, `stum`, and the v1 access model |

## Pending decisions

| ID | Question | Needed by |
|---|---|---|
| P-001 | Duplicate upload by SHA-256: return existing asset or reject with 409? | M2 |
| P-002 | Multiple subtitle tracks per media in the first UI, or one default? | M5 |
| P-003 | Optimistic concurrency for entry edits (`expected_updated_at`)? | M5 |
| P-004 | Light theme in v1 or dark-first? | M1/M2 |
| P-005 | Media deletion/retention policy | M7 |
| P-006 | Final font self-hosting choice | M1 |

## Change process

- A new decision requires an ADR (or an amendment to an existing one) and an
  entry here.
- Architecture, scope, licence, and security changes require human approval.
- Rejected decisions stay recorded with the reason, so they are not
  re-litigated accidentally.

## Rejected / deferred

| Idea | Reason |
|---|---|
| Redis + Celery | Extra service, unnecessary at single-node scale (ADR-0005) |
| Bundling `stum` | CC-BY-NC conflicts with MIT distribution (ADR-0003/0007) |
| Auth in v1 | Scope; local single-user boundary documented instead (ADR-0007) |
| TypeScript 7 | Ecosystem compatibility unproven; pin 5.9 (ADR-0001) |
| Installing npm `watermelon-ui` | Unrelated package, not Watermelon UI (ADR-0006) |
