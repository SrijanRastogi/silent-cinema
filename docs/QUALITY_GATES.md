# QUALITY_GATES.md

This file defines the gates that every change must pass. It is loaded as an
instruction file by OpenCode (`opencode.jsonc`) and is binding under
`AGENTS.md`.

**Current applicability:** M0 is documentation-only. Executable gates begin in
M1. Until then, commands marked "planned" must not be reported as run.

## 1. Gate levels

| Gate | When | What must pass |
|---|---|---|
| G0 — Docs | Every change | Links resolve, claims are labelled, docs match reality |
| G1 — Static | Every code change | Ruff, format, MyPy, ESLint, Prettier, `tsc --noEmit` |
| G2 — Unit | Every code change | Pytest unit, Vitest |
| G3 — Integration | DB/API/worker/export changes | PostgreSQL migrations up/down, API, worker, serializers |
| G4 — E2E | Milestone close | Playwright primary workflow + failure paths |
| G5 — Release | Release only | Security, licence, container build, clean-machine deploy |

A change is mergeable only when its required gates pass. "Required" is
determined by the files touched, not by optimism.

## 2. Per-feature workflow

```text
0. CONTEXT     Read AGENTS → PLAN → STATUS → DECISIONS → this file
1. DECLARE     Task sentence, acceptance criteria, file list, risks
2. BASELINE    Run the gate and record the starting state
3. RED         Write a failing test for new behaviour (where testable)
4. IMPLEMENT   Smallest change that satisfies the criteria
5. TARGETED    Run the specific tests/lints for the touched area
6. FULL GATE   Run make check (or the documented equivalent)
7. AUDIT       Inspect git diff for scope, secrets, debug code, generated files
8. DOCS        Update STATUS, CHANGELOG, and affected design docs
9. REPORT      Commands + outputs + limitations, tagged claims
10. STOP       Do not continue into the next task or milestone
```

### Step 1 — Declare template

```text
Task:
Acceptance criteria:
Files to change:
Dependencies (new?):
Risk / unknowns:
Gate level required:
```

If the file list changes during implementation, stop and re-declare. A change
that touches files outside the declaration is a scope breach, even if the code
is correct.

### Step 2 — Baseline

Record the result before editing. If the baseline is already failing, say so;
do not attribute pre-existing failures to your change, and do not "fix" them
silently.

### Step 3 — Red

For logic changes, the test must fail for the right reason before the
implementation. If a test cannot be written first, explain why in the report.

## 3. Hallucination controls

### 3.1 Claim labels

Every statement in a status report, PR description, or doc update carries one
of:

- `[VERIFIED]` — backed by a command output, file read, or official source.
- `[UNVERIFIED]` — believed but not checked.
- `[PLANNED]` — designed, not built.
- `[BLOCKED]` — cannot proceed; reason stated.
- `[FAILED]` — attempted and did not work.

Unlabelled claims are treated as unverified.

### 3.2 Verification rules

Before asserting any of the following, verify it:

| Claim type | Required check |
|---|---|
| A command passes | Run it; include the tail of the output |
| A package exists | Registry metadata or official docs |
| A version supports our runtime | Release metadata, classifiers, or install attempt |
| An API exists | Official docs or the running OpenAPI schema |
| A file/path exists | `ls`, `find`, or read it |
| A licence | Repository `LICENSE` or registry metadata |
| A benchmark/accuracy | Reproducible method and data; otherwise do not state a number |
| A test is skipped | Say "skipped", never "passing" |

### 3.3 Prohibited fabrications

- Invented test results, coverage, timings, or OCR accuracy.
- Invented endpoints, fields, env vars, or package names.
- Claiming CI ran when it did not.
- Claiming a review occurred when Antigravity was unreachable.
- Presenting a mockup or static data as working functionality.
- "Should work" phrased as "works".

### 3.4 Known traps in this project

- `watermelon-ui` on npm is **not** Watermelon UI. Use the shadcn registry.
- `stum` is **not** an OCR library to import; it is a CLI with a restrictive
  licence.
- shadcn currently offers Base UI and Radix variants; do not mix primitives
  without an ADR.
- TypeScript 7 exists but the project pins 5.9 for ecosystem stability.
- Python 3.14 is the system default; the project targets 3.13.
- `postgresql-contrib` has no candidate on Ubuntu 26.04.
- Tesseract language packs existing on disk does not mean the language is
  supported; it means it is installed.

## 4. Error-checking pipeline

### 4.1 Backend (planned, M1)

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy apps
uv run pytest -m "not integration and not media"
uv run pytest -m integration          # requires PostgreSQL
uv run alembic upgrade head
uv run alembic downgrade base
uv run alembic upgrade head
```

### 4.2 Frontend (planned, M1)

```bash
npm --prefix apps/web run lint
npm --prefix apps/web run format:check
npm --prefix apps/web run typecheck
npm --prefix apps/web run test
npm --prefix apps/web run build
```

### 4.3 Contract (planned, M1)

```bash
uv run python scripts/export_openapi.py
npm --prefix apps/web run generate:api
git diff --exit-code -- apps/web/src/api/schema.d.ts
```

### 4.4 E2E (planned, M7, smoke earlier)

```bash
npm --prefix tests/e2e run test
```

### 4.5 Documentation (M0 onward)

- Every relative link resolves.
- Every command block is either marked planned or has been run.
- Status labels match `docs/STATUS.md`.
- No doc claims a feature that `PLAN.md` marks as planned.

## 5. Diff audit

Before reporting completion, inspect:

```bash
git status --short
git diff --stat
git diff
```

Check for:

- [ ] Files outside the declared list
- [ ] Secrets, tokens, passwords, `.env`
- [ ] Media, models, databases, build output
- [ ] Debug prints, `console.log`, `breakpoint()`
- [ ] Commented-out code
- [ ] New dependencies without an ADR
- [ ] Disabled tests or lint rules
- [ ] Unrelated formatting or renames
- [ ] Generated files edited by hand
- [ ] Claims in docs that are not true

## 6. Scope and tangent control

- The milestone in `PLAN.md` is the scope boundary.
- A new idea goes to `BACKLOG.md` immediately, with a one-line rationale.
- Do not create directories, packages, or interfaces "for later".
- Do not refactor code you are not changing for the task.
- Do not upgrade dependencies as part of a feature.
- If a dependency forces a change outside scope, stop and ask.

## 7. Stop conditions

Stop and report instead of improvising when:

- The baseline gate fails for reasons unrelated to the task.
- A required tool or service is missing.
- A dependency needs a licence decision.
- A schema or API change contradicts an approved document.
- The task requires touching files outside the declared list.
- A test cannot be made deterministic.
- The acceptance criteria are ambiguous.
- Continuing would exceed the milestone.

## 8. Evidence block

Every completion report includes:

```text
Milestone / task:
Changed:
Acceptance criteria met:
Commands run:
  <command>
  → <actual result, including failures>
Tests:
  passed: N
  failed: N
  skipped: N (reasons)
Known issues:
Deviations:
Next proposed task:
```

## 9. Status update protocol

After a task, update `docs/STATUS.md` with:

- current milestone and active task,
- completed items,
- blockers,
- latest gate results with timestamp,
- files changed,
- next approved action.

Update `CHANGELOG.md` for user-visible changes. Update `PLAN.md` only when
scope or acceptance criteria change with approval.

## 10. Review checklist (conductor)

- [ ] Scope matches the approved milestone.
- [ ] Acceptance criteria are objectively demonstrated.
- [ ] Gate output is real and current.
- [ ] No disabled checks or skipped tests presented as passing.
- [ ] Schema/API/docs are consistent.
- [ ] Security boundaries respected.
- [ ] Licence implications recorded.
- [ ] No fabricated claims.
- [ ] Findings logged in `docs/REVIEW_LOG.md` with severity.
