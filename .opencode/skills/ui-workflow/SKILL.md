---
name: UI Workflow
description: Build or review frontend UI using the project's archival-workstation design system, shadcn/ui primitives, selected Watermelon UI registry blocks, and accessibility requirements.
---

# UI Workflow

Use this skill for any frontend, styling, layout, or component work.

## Mandatory first step

Load these built-in skills before designing or coding:

1. `frontend-design` — visual direction and non-templated aesthetics.
2. `web-design-guidelines` — interface and accessibility review.
3. `vercel-react-best-practices` — React/Next performance patterns.

Then read `docs/UI.md` and the relevant page requirements in `PLAN.md`.

## Design constraints

- Archival workstation, not a generic admin template.
- Warm neutral palette, film-amber accent, serif display type, monospace
  timecodes.
- Dark and light tokens defined in `docs/UI.md`; no arbitrary colours.
- No fake metrics, charts, counts, or sample data.
- Status is never colour-only.
- Motion is restrained and respects `prefers-reduced-motion`.

## Component rules

- Use shadcn/ui primitives for buttons, inputs, dialogs, menus, tables, tabs,
  tooltips, and toasts.
- Watermelon UI is a **shadcn registry**, not an npm package.
  - Install a specific block:
    `npx shadcn@latest add https://registry.watermelon.sh/r/<slug>.json`
  - Review the generated code; remove decorative animation from editing views.
  - Record the source URL and date in the component header and
    `THIRD_PARTY_NOTICES.md`.
- Never install the npm package `watermelon-ui`.
- Do not mix Base UI and Radix primitives without an ADR.
- Keep page files small; extract domain components (`TimecodeInput`,
  `EntryRow`, `JobStateBadge`).

## Required states

Every asynchronous view must implement: loading, empty, error, success, and
disabled/unauthorized where applicable. Errors must be actionable and safe.

## Accessibility

- WCAG 2.2 AA.
- Labels, visible focus, keyboard paths, `aria-live` errors.
- Video controls reachable; subtitle overlay toggleable.
- Check at 1280×720, 1366×768, 1920×1080.

## Testing

- Component tests for timecode validation, overlaps, review state, job state.
- Playwright for the primary workflow.
- Axe checks on primary pages; manual keyboard pass.

## Report

Include screenshots only from the running app with real data, and state which
flows are not yet wired.
