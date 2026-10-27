# TESTING.md

Status: **strategy for M1+. No test suite exists yet.** Commands below are the
intended interface; they become real when the corresponding milestone lands.
Never report them as passing before then.

## 1. Principles

- Tests are evidence, not decoration.
- Deterministic and offline by default. No network calls in unit or integration
  tests.
- Test behaviour at the boundary: HTTP, database, files, filesystem, generated
  subtitle files.
- Mock only external boundaries (OCR binary, clock, object storage). Never mock
  the module under test.
- Every bug fix includes a regression test.
- A skipped test is not a passing test.

## 2. Test layers

| Layer | Scope | Runs in |
|---|---|---|
| Unit (backend) | Pure logic: timecode, serializers, validation, state machine, error mapping | `pytest -m "not integration"` |
| Unit (frontend) | Components, hooks, form validation | `vitest run` |
| Integration | DB, migrations, storage, API, worker | `pytest -m integration` with PostgreSQL |
| Contract | OpenAPI schema vs committed generated types | CI |
| E2E | Primary workflow through a browser | Playwright against real services |
| Media integration | Real FFmpeg/Tesseract on small fixtures | Explicit marker, not in default unit run |

## 3. Backend coverage

### 3.1 Unit

- Microseconds ↔ SRT/VTT timecode conversion, including rounding boundaries
  (`999499 µs`, `999500 µs`), hours, and negative/overflow rejection.
- SRT serialization: numbering, blank lines, CRLF/LF policy, multiline text,
  trailing whitespace.
- WebVTT serialization: `WEBVTT` header, timestamp format (`hh:mm:ss.mmm`),
  cue identifiers, no `-->` in text without escaping.
- Unicode: accented Latin, Devanagari, emoji, RTL, combining marks, zero-width
  characters, newlines.
- Timestamp validation: `end > start`, non-overlap, ordering, zero-length,
  beyond media duration.
- Job state machine: every valid transition accepted; every invalid transition
  rejected; retry rules.
- File validation: extension, declared content type, size, empty file, magic
  bytes/ffprobe error mapping.
- Error mapping to stable codes and HTTP statuses.

### 3.2 Integration

- Alembic `upgrade head` and `downgrade base` on a fresh database.
- Upload → media row → job creation.
- Worker claim, lease renewal, stale recovery, cancellation.
- Worker result persistence and idempotent retry.
- Intertitle listing and review status changes.
- Subtitle entry create/update/delete/reorder, overlap rejection, deferred
  constraints.
- Export creation, validation, download, and re-import of the generated SRT/VTT.
- Cleanup after success, failure, and cancellation.
- Path containment under a temporary storage root.

### 3.3 E2E (Playwright)

Primary workflow:

1. Dashboard loads with real empty state.
2. Upload a small synthetic video.
3. Start processing.
4. Observe real state transitions (no simulated progress).
5. Review detected intertitles.
6. Correct a subtitle.
7. Export SRT.
8. Download and validate the file.
9. Confirm the preview shows the corrected subtitle at the expected time.

Failure paths: malformed media, unsupported input, OCR failure, worker failure,
invalid timestamps, export rejection.

## 4. Fixtures

- `tests/fixtures/` contains generators and small metadata, not large media.
- A synthetic film is generated with FFmpeg: black frames + high-contrast text
  cards at known times, constant frame rate, known duration.
- A variable-frame-rate fixture is generated for timebase tests.
- A mirrored-text card fixture is generated for detector robustness.
- Fixtures are deterministic and under a few megabytes.
- No copyrighted films, no private data, no models in Git.
- OCR language fixtures must be labelled with the language actually tested.

## 5. Commands

Backend, frontend, and media gates are implemented. `make e2e` is not: the
Playwright suite and primary workflow do not exist yet.

```bash
make check              # backend lint/type/unit + frontend lint/type/unit/build
make test               # backend unit + frontend unit
make test-integration   # PostgreSQL required
make test-media         # FFmpeg + Tesseract required, explicit marker
make migrate            # alembic upgrade head
make migrate-down       # alembic downgrade -1
make docs-check         # links, claim labels, API/doc consistency
```

`make e2e` is planned for M5/M6 and does not exist yet.

Backend:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -m "not integration and not media"
uv run pytest -m integration
```

Frontend:

```bash
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build
```

## 6. Coverage policy

Targets, once measured:

- 90% line coverage for `subtitles/`, `jobs/`, and validation modules.
- 80% line coverage for backend application code overall.
- 70% for frontend components with logic.

Rules:

- Coverage is a signal, not a substitute for assertions.
- A change must not reduce coverage of the modules it touches without a written
  justification in the PR.
- Generated code, migrations, and configuration are excluded.
- No coverage threshold may be lowered to make CI green.

These targets are **[PLANNED]**; no coverage number has been measured yet.

## 7. Media-processing tests

- Unit tests never require Tesseract, FFmpeg, or `stum`.
- Media tests use the synthetic fixture and assert structural properties
  (interval count, ordering, time ranges, text presence), not exact OCR strings
  across engines.
- The optional `stum` adapter is tested against a fake executable that emits a
  known SRT and known error exit codes. A real `stum` run is a manual,
  documented check.
- OCR accuracy claims require a labelled corpus and a recorded method; none
  exists yet.

## 8. CI gates

`.github/workflows/ci.yml` (M1) runs, on every pull request:

1. Backend: install, Ruff, format check, MyPy, unit tests.
2. Frontend: `npm ci`, ESLint, `tsc --noEmit`, Vitest, production build.
3. Integration: PostgreSQL service, migrations up/down, integration tests.
4. Contract: OpenAPI generation and type consistency.
5. E2E smoke: Playwright on the primary path.
6. Security: secret scan, dependency audit, licence inventory.
7. Docker: image build.

Actions are pinned by commit SHA. A failing job is never neutralised by
`continue-on-error`.

## 9. Known gaps (current)

- No test suite exists.
- No real silent-film corpus; no accuracy benchmark.
- Hindi and other language packs are installed at the OS level only; no OCR
  validation has been performed.
- Variable-frame-rate behaviour is designed but untested.
- `stum` installation on Python 3.13 is unverified.
- Playwright browsers are not installed.
- CI has never run (no remote repository).

## 10. Evidence

`docs/STATUS.md` records each gate run with the exact command and a short
summary of actual output. Test reports and screenshots are stored as CI
artifacts, not committed.
