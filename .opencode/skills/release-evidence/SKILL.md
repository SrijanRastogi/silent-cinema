---
name: Release Evidence
description: Report progress and close milestones with labelled claims, exact commands and outputs, honest limitations, updated status files, and no fabricated results.
---

# Release Evidence

Use when reporting a completed task, closing a milestone, or writing release
notes.

## Claim labels

Every statement carries one of:

- `[VERIFIED]` — backed by a command output, file read, or official source.
- `[UNVERIFIED]` — believed, not checked.
- `[PLANNED]` — designed, not built.
- `[BLOCKED]` — cannot proceed; reason stated.
- `[FAILED]` — attempted and failed.

Unlabelled claims are treated as unverified.

## Report template

```text
Milestone / task:
What changed:
Acceptance criteria met:
Commands run:
  <command>
  → <actual output summary, including failures>
Tests:
  passed: N
  failed: N
  skipped: N (reason per skip)
Known issues:
Deviations from plan:
Next proposed task:
```

## Rules

- Include the command, not just the conclusion.
- Show failures and partial results.
- Never claim CI ran without a run URL or log.
- Never claim a review occurred when the reviewer was unreachable.
- Never present a mock or fixture as production evidence.
- State what was **not** tested.
- Do not round "2 of 3 passed" up to "passing".

## Status updates

Update `docs/STATUS.md` with:

- current milestone and active task,
- completed items,
- blockers,
- latest gate results and timestamp,
- files changed,
- next approved action.

Update `CHANGELOG.md` for user-visible changes and `PLAN.md` only for approved
scope changes.

## Milestone close

Before declaring a milestone complete:

1. Every acceptance criterion is demonstrated.
2. Required gates pass (G0–G5 as applicable).
3. Migration up/down evidence exists if schema changed.
4. Documentation matches behaviour and limitations.
5. `docs/REVIEW_LOG.md` has a review entry or an explicit "not reviewed" note.
6. Stop; do not start the next milestone without approval.
