---
name: Project Context
description: Load the project's current milestone, status, decisions, and constraints before starting any task in the silent-cinema repository.
---

# Project Context

Use this skill at the start of **every** task in this repository.

## Workflow

1. Read, in order:
   - `AGENTS.md`
   - `PLAN.md`
   - `docs/STATUS.md`
   - `docs/DECISIONS.md`
   - `docs/QUALITY_GATES.md`
   - the ADR relevant to the area
2. Summarize back to yourself:
   - current milestone,
   - active task (or "none"),
   - acceptance criteria that apply,
   - blockers,
   - files likely involved.
3. Check that the requested work belongs to the current milestone.
4. If it does not, stop and propose adding it to `BACKLOG.md`.

## Rules

- `docs/STATUS.md` is the live state; `PLAN.md` is the roadmap.
- A document marked "planned" is not implemented.
- Do not infer progress from file existence; check the status file and the
  actual code.
- If `docs/STATUS.md` is stale, update it before starting new work.
- Never claim a milestone passed without evidence in `docs/STATUS.md`.

## Output

A short context block:

```text
Milestone:
Task:
Acceptance criteria:
Files:
Blockers:
```
