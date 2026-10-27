# CONTRIBUTING.md

## Before you start

Read `AGENTS.md`, `PLAN.md`, and `docs/STATUS.md`. Contributions outside the
current milestone are deferred to `BACKLOG.md` unless the human owner approves
a scope change in `docs/DECISIONS.md`.

By contributing, you agree that your work is licensed under the MIT licence in
`LICENSE`.

## Setup

```bash
git clone <repository-url>
cd silent-cinema
cp .env.example .env
make doctor
make bootstrap
make migrate
```

`make` targets are introduced in M1. Until then, follow `DEPLOYMENT.md`
manually and do not claim the application runs.

## Branching

- `main` is protected and releasable.
- Work on `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`, or
  `chore/<short-name>`.
- One milestone concern per branch.
- Rebase or merge `main` before requesting review; do not force-push shared
  branches.

Commit messages:

```text
<area>: <imperative summary>

<why, not a restatement of the diff>

Refs: M2, #123
```

Areas: `api`, `web`, `worker`, `db`, `media`, `subtitles`, `docs`, `ci`.

## Pull requests

Every PR states:

1. The milestone and task.
2. Acceptance criteria addressed.
3. Files/areas changed.
4. Exact commands run and their results.
5. Known limitations or follow-ups.
6. Screenshots for UI changes (real data, no mockups presented as working).

Reviewers check `docs/QUALITY_GATES.md`. A PR that fails a gate is not merged;
a gate is never disabled to make a PR pass.

## Coding standards

- Python: Ruff, MyPy, 4-space indentation, typed public functions.
- TypeScript: strict mode, ESLint, Prettier, functional components.
- SQL: Alembic migrations, explicit constraints and indexes.
- Docs: Markdown, one sentence per line where practical, no unverifiable
  claims.
- Tests accompany behaviour changes.
- No new dependency without an ADR and licence review.

## UI contributions

- Follow `docs/UI.md`.
- Load the `ui-workflow` skill, which in turn requires the built-in
  `frontend-design`, `web-design-guidelines`, and
  `vercel-react-best-practices` skills.
- Use shadcn/ui primitives. Watermelon UI blocks are copied from the MIT
  registry and attributed; the npm package `watermelon-ui` is unrelated and
  must not be installed.
- Accessibility is part of acceptance, not a follow-up.
- No invented analytics, metrics, or sample data in the product UI.

## Media and test data

- Do not commit films, frames, OCR models, or generated subtitles.
- Use the synthetic fixture generator.
- Do not upload private or copyrighted media to CI or issue trackers.

## Documentation updates

Every change updates, as applicable:

- `README.md` if setup/features/limits changed,
- `PLAN.md` if scope/acceptance changed,
- `docs/STATUS.md` always,
- `CHANGELOG.md` for user-visible changes,
- `API.md` / `DATABASE.md` / `ARCHITECTURE.md` for contract changes,
- `THIRD_PARTY_NOTICES.md` for dependencies.

## Review expectations

- Review findings are logged in `docs/REVIEW_LOG.md` with severity
  (`blocker`, `major`, `minor`, `nit`) and resolution.
- Disagreements about architecture or scope go to the human owner.
- "It works on my machine" is not evidence; include the command and output.
