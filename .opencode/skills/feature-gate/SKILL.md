---
name: Feature Gate
description: Enforce the pre-change declaration, test-first loop, full quality gate, diff audit, documentation update, and honest evidence report for every code change.
---

# Feature Gate

Use this skill for **any** code, schema, CI, or configuration change.

Reference: `docs/QUALITY_GATES.md` (binding).

## Before editing

Produce and keep this block:

```text
Task:
Acceptance criteria:
Files to change:
New dependencies:
Risk / unknowns:
Gate level: G0 | G1 | G2 | G3 | G4
Baseline result:
```

Then:

1. Run the baseline gate, or state why it cannot run.
2. Write a failing test for new logic where testable.
3. Confirm every file is inside the declared list and the current milestone.

If the file list changes, stop and re-declare.

## While implementing

- Smallest change that satisfies the criteria.
- No refactors, renames, dependency upgrades, or formatting sweeps.
- No fake data, dead buttons, or placeholder success paths.
- No disabled tests or lint rules.
- No new dependency without an ADR and licence check.

## After editing

1. Targeted tests.
2. Full gate (`make check` or documented equivalent).
3. Migration up **and** down if schema changed.
4. Regenerate OpenAPI/types if contracts changed.
5. `git status --short`, `git diff --stat`, `git diff`.
6. Audit for scope creep, secrets, debug code, generated files.
7. Update `docs/STATUS.md`, `CHANGELOG.md`, and affected docs.
8. Report with the evidence block from `docs/QUALITY_GATES.md` §8.

## Stop conditions

Stop and report if:

- the baseline is failing for unrelated reasons,
- a tool/service is missing,
- a dependency needs a licence decision,
- the work requires files outside the declaration,
- acceptance criteria are ambiguous,
- the change would cross the milestone boundary.

## Prohibited

- Saying "tests pass" without output.
- Marking skipped as passed.
- Turning off a check to go green.
- Continuing into the next task automatically.
