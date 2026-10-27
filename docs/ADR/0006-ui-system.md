# ADR-0006 — UI system: shadcn/ui and Watermelon UI

- **Status:** Accepted (M0)
- **Date:** 2026-10-27

## Context

The product needs a distinctive archival-workstation interface, not a generic
admin template. The human owner asked to use shadcn/ui and Watermelon UI.
Watermelon UI's distribution model and licence needed verification.

## Decision

1. **shadcn/ui is the component foundation** (MIT). Components are generated
   into the repository and owned by the project.
2. **Watermelon UI is used as a shadcn registry**, not an npm dependency:
   - MIT licensed (verified on the platform and registry repositories),
   - install specific blocks with the shadcn CLI from
     `https://registry.watermelon.sh/r/<slug>.json`,
   - copy only what is needed, review it, remove decorative animation from
     editing surfaces, and attribute the source.
3. **Do not install the npm package `watermelon-ui`.** It is an unrelated 2018
   ISC package and not WatermelonCorp.
4. Design direction follows `docs/UI.md`: serif display type, IBM Plex UI/mono,
   warm neutral palette, film-amber accent, archival-workstation layout.
5. Accessibility target: WCAG 2.2 AA.
6. No fake metrics, fake charts, or invented dashboard data.

## Rationale

- shadcn gives accessible primitives and local ownership without a runtime
  component dependency.
- Watermelon provides production-style compositions but is a registry, so
  copying is the supported path.
- Avoids supply-chain confusion with the unrelated npm package.
- A distinct visual system prevents the project from reading as a template.

## Consequences

- Copied components must be maintained by us.
- Every copied Watermelon block requires a source URL and date in
  `THIRD_PARTY_NOTICES.md` or the component header.
- shadcn's Base UI vs Radix variant must be consistent; mixing requires an ADR.
- Vite 8 + shadcn CLI compatibility is verified in M1 before adoption is
  considered complete.
