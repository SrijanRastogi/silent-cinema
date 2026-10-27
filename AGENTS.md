# AGENTS.md — Operating Contract

This file is binding for every coding agent (OpenCode, Antigravity, or any
future contributor) working in this repository. It is loaded automatically by
OpenCode. When this file conflicts with a casual instruction in chat, this file
wins unless the human owner explicitly approves an exception and records it in
`docs/DECISIONS.md`.

## 1. Project identity

**Silent Cinema in Your Language** is a local-first web application for
extracting intertitles from silent films, correcting OCR output, and exporting
valid SRT/WebVTT subtitles. It is a modular monolith: React frontend, FastAPI
backend, and a PostgreSQL-backed worker.

Current milestone and status live in `docs/STATUS.md`. The authoritative
roadmap is `PLAN.md`. Neither may be updated to claim work that is not
implemented and verified.

## 2. Read before you touch anything

Before any task, in this order:

1. `AGENTS.md` (this file)
2. `PLAN.md` — current milestone, acceptance criteria, dependencies
3. `docs/STATUS.md` — active task, blockers, last verified results
4. `docs/DECISIONS.md` and the relevant `docs/ADR/*.md`
5. `docs/QUALITY_GATES.md` — the checklist you must pass

If any of these files are missing or contradictory, stop and report. Do not
guess.

## 3. Non-negotiable rules

### 3.1 Evidence, not confidence

- Every factual claim in a report must be backed by a command output, a file
  you read, or an official document you cited.
- Tag claims: `[VERIFIED]`, `[UNVERIFIED]`, `[PLANNED]`, `[BLOCKED]`,
  `[FAILED]`.
- Never say "tests pass", "build succeeds", "OCR works", or "deployed" without
  showing the command and its actual result.
- A skipped or not-run test is `[PLANNED]` or `[BLOCKED]`, never "passing".
- Do not invent file paths, endpoints, package names, versions, licences, or
  benchmark numbers. Verify against the registry, repository, or docs.

### 3.2 No scope expansion

- Implement only the current milestone and the explicitly approved task.
- Anything else goes to `BACKLOG.md` with a short rationale. Do not implement
  it, and do not create scaffolding "for later".
- If a task seems to require work outside the milestone, stop and ask. A
  documented dependency may justify re-ordering milestones; convenience does
  not.

### 3.3 Inspect before changing

- Read the files you intend to change and their neighbours.
- Check `git status` and `git diff` before editing.
- Reuse existing patterns instead of inventing parallel ones.
- Never delete or rewrite work you do not understand.
- Never overwrite uncommitted user changes. If the working tree is dirty,
  report it and ask before proceeding.

### 3.4 Dependencies require review

No new runtime dependency may be added without:

1. Confirming it exists and the version supports Python 3.13 / Node 24.
2. Reading its official documentation or repository.
3. Checking its licence and redistribution terms.
4. Recording the decision in `docs/ADR/` and `THIRD_PARTY_NOTICES.md`.
5. Pinning or constraining the version in the lockfile.

The approved stack in Section 4 is already reviewed at the ADR level. New
libraries inside an approved category still need a licence check.

### 3.5 No fake functionality

- No buttons that do nothing.
- No hardcoded success responses.
- No simulated progress presented as real backend progress.
- No placeholder data shown as user data.
- If something is unavailable, say so in the UI with an actionable message.
- Mocked services are allowed only in tests, never in a production code path.

### 3.6 Security by default

- Treat every uploaded file as hostile.
- Validate extension, size, content type, and actual media streams.
- Generate server-side storage names; never trust a client filename in a path.
- Never interpolate user input into a shell command. Use argument arrays.
- Apply timeouts and resource limits to external processes.
- Do not expose stack traces, absolute paths, or secrets in API responses.
- Do not commit `.env`, media, models, or credentials.
- Bind to `127.0.0.1` by default in development.

### 3.7 Minimal diff

- One concern per change.
- No drive-by refactors, formatting sweeps, renames, or dependency upgrades.
- If a file outside your declared change list must be touched, stop and
  re-declare the plan first.
- Generated files are never edited by hand.

### 3.8 Completion requires evidence

A task is complete only when its acceptance criteria pass, the quality gate
passes, and `docs/STATUS.md` records the exact commands and results. "It should
work" is not completion.

## 4. Approved stack

| Layer | Approved choice |
|---|---|
| Language (backend) | Python 3.13 |
| API | FastAPI, Pydantic v2, Uvicorn |
| ORM / migrations | SQLAlchemy 2.x, Alembic, psycopg 3 |
| Database | PostgreSQL 18 |
| Queue | PostgreSQL table + `FOR UPDATE SKIP LOCKED` (no Redis in v1) |
| Media | FFmpeg / ffprobe (argv arrays only), OpenCV headless |
| OCR | Tesseract via pytesseract; optional external `stum` CLI adapter |
| Frontend | React 19, Vite 8, TypeScript 5.9 (strict), Tailwind CSS 4 |
| UI system | shadcn/ui + selected Watermelon UI registry blocks (MIT) |
| Routing / state | React Router 7, TanStack Query 5 |
| Forms | React Hook Form 7 + Zod 4 |
| Tests | Pytest, Vitest, React Testing Library, Playwright |
| Quality | Ruff, MyPy, ESLint, Prettier, Vitest, Playwright |
| Runtime | Node 24, npm with committed lockfile |
| Deployment | Docker Compose for local parity; explicit migrations |

Deviations require an ADR approved by the human owner. See
`docs/ADR/0001-approved-stack.md`.

## 5. Repository conventions

Target structure (do not create empty directories before they are needed):

```text
apps/api/            FastAPI application (routes, services, models, schemas)
apps/web/            React application
apps/worker/         Worker entrypoint and job runner
tests/               Backend unit/integration tests and fixtures
tests/e2e/           Playwright tests
docs/                Architecture, decisions, status, ADRs
scripts/             Repeatable developer scripts
.github/workflows/   CI pipelines
```

Naming:

- Python: `snake_case`; modules by responsibility, not by layer alone.
- TypeScript: `camelCase` for values, `PascalCase` for components/types.
- Database: plural `snake_case` tables, `snake_case` columns, `*_us` for
  microsecond timestamps, `*_at` for UTC instants.
- API: `/api/v1/...`, plural resources, stable error codes.
- Files: kebab-case for docs, lowercase for Python modules.

Boundaries:

- Routes do not contain business logic; services do.
- Services do not import FastAPI request objects.
- The worker calls the same services as the API; it must not duplicate logic.
- The detector/OCR implementation sits behind an interface; the pipeline never
  imports Tesseract or `stum` directly.
- Frontend never invents API fields; types are generated from OpenAPI.

## 6. Coding standards

### Python

- Ruff lint + format, MyPy on application packages.
- Full type annotations on public functions.
- Pydantic models at the boundary; SQLAlchemy models stay in the persistence
  layer.
- No bare `except`; map errors to typed error codes.
- No blocking work inside request handlers.
- `subprocess` only with `list[str]` arguments, `shell=False`, timeout, and
  captured output.

### TypeScript / React

- `strict: true`; no `any` without a written justification.
- Server state through TanStack Query; form state through React Hook Form.
- Components small and composable; no giant page files.
- Accessible by default: labels, focus states, keyboard paths, reduced motion.
- No client-side secrets.
- No fake loading animations; loading states reflect real requests.

### SQL / data

- Every schema change is an Alembic migration.
- Foreign keys, check constraints, and indexes are part of the design, not an
  afterthought.
- Timestamps are UTC. Durations/media positions are integer microseconds.
- Never auto-create tables at application startup in production.

### Documentation

- Documentation must distinguish implemented, tested, planned, blocked, and
  failed.
- Every milestone updates `README.md`, `PLAN.md`, `docs/STATUS.md`,
  `CHANGELOG.md`, and any affected design doc.
- API docs must match the generated OpenAPI schema.

## 7. Testing requirements

- New logic requires tests in the same change.
- Bug fixes require a regression test that fails before the fix.
- Backend: unit tests for timestamps, serializers, validation, state machine,
  and error mapping. Integration tests for DB, migrations, uploads, worker
  persistence, edits, exports, and cleanup.
- Frontend: component tests for editor behaviour and validation; Playwright for
  the primary workflow.
- Tests must be deterministic and independent of network access.
- Heavy media/OCR tests live behind an explicit marker and are not required for
  ordinary unit runs.
- Do not mock the code under test. Mock only external boundaries (OCR binary,
  clock, filesystem where appropriate).
- Coverage policy and known gaps live in `TESTING.md`.

## 8. Pre-feature checklist (mandatory)

Copy this into your working notes and complete it before editing:

```text
[ ] Read AGENTS.md, PLAN.md, docs/STATUS.md, docs/DECISIONS.md
[ ] Task stated in one sentence
[ ] Acceptance criteria listed
[ ] Files to change listed (nothing outside the milestone)
[ ] Dependencies checked (approved, or ADR pending)
[ ] Baseline recorded (make check, or why it cannot run)
[ ] Test-first plan written for new logic
[ ] Risks / unknowns listed
```

If any box cannot be ticked, stop and report.

## 9. Post-feature checklist (mandatory)

```text
[ ] Targeted tests written and run
[ ] Full quality gate run (make check)
[ ] Migration up/down verified when schema changed
[ ] API schema regenerated and consistent
[ ] git diff inspected for scope creep, secrets, debug code
[ ] Docs updated (README/PLAN/STATUS/CHANGELOG/affected docs)
[ ] Claims tagged and evidenced
[ ] Known failures reported, not hidden
[ ] Milestone boundary respected
```

## 10. Definition of Done

A task is done when:

1. Acceptance criteria in `PLAN.md` are met.
2. `docs/QUALITY_GATES.md` passes, or every exception is documented and
   approved.
3. No new warnings, skipped tests, or disabled checks.
4. Documentation matches reality, including limitations.
5. `docs/STATUS.md` records commands, results, and the next approved action.

## 11. Tangent protocol

When you notice an improvement outside scope:

1. Stop implementing it.
2. Add an entry to `BACKLOG.md` with context and why it is deferred.
3. Continue the current task.

Do not "quickly fix" unrelated code. Do not add abstractions for hypothetical
future needs. Do not add placeholder packages.

## 12. Skill usage

Project skills live in `.opencode/skills/`. Load the relevant skill before the
work, not after:

- `project-context` — starting any task
- `feature-gate` — any code change
- `ui-workflow` — any frontend or design work; it also requires loading the
  built-in `frontend-design`, `web-design-guidelines`, and
  `vercel-react-best-practices` skills
- `backend-contract` — API, schemas, errors
- `media-subtitles` — FFmpeg, OCR, timecodes, SRT/VTT
- `release-evidence` — reporting and milestone close-out

## 13. Coordination

- OpenCode is the implementation lead.
- Antigravity is the conductor/reviewer when available.
- The human owner is the final decision-maker for architecture, scope, and
  licences.
- If Antigravity is unreachable, record it in `docs/REVIEW_LOG.md` and
  `docs/STATUS.md`. Never claim a review happened.
- Reviews are recorded with severity and resolution status in
  `docs/REVIEW_LOG.md`.

## 14. Prohibited actions

- Committing media, models, secrets, `.env`, databases, or build output.
- Running `git push`, publishing packages, or deploying without explicit
  approval.
- Force-pushing or rewriting history.
- Disabling tests, lint rules, or type checks to make a gate pass.
- Installing the unrelated npm package `watermelon-ui` (it is not Watermelon
  UI; the real project is a shadcn registry).
- Adding machine translation, TTS, dubbing, social features, payments, or
  multi-tenancy without an approved milestone.
- Copying `stum` source code or redistributing its models.
- Shelling out with `shell=True` or string-interpolated commands.

## 15. Commands

Commands become real in M1. Until then, `make` targets do not exist and must
not be reported as passing. The intended interface is documented in
`docs/QUALITY_GATES.md` and `TESTING.md`.
