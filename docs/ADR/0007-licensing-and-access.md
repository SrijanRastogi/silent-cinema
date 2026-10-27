# ADR-0007 — Licensing, `stum`, and the v1 access model

- **Status:** Accepted (M0)
- **Date:** 2026-10-27
- **Deciders:** Human owner

## Context

The project is open source. The most relevant prior art, `stum`, is licensed
CC-BY-NC 4.0. The product brief requires a single-user workflow but mentions
job ownership, without defining an authentication model.

## Decision

### Licensing

1. The repository is **MIT** licensed.
2. `stum` is **not bundled, vendored, copied, or redistributed**.
3. `stum` is an optional external CLI adapter, disabled by default.
4. Enabling it is a non-commercial use of a CC-BY-NC tool; this is disclosed in
   the UI, `DEPLOYMENT.md`, and `THIRD_PARTY_NOTICES.md`.
5. Our MIT licence does not grant rights to `stum`, and licensing our own code
   under CC-BY-NC would not grant additional rights to `stum`.

### Access model

1. v1 is a **single-user, local-first** application.
2. No authentication, accounts, roles, or tenancy are implemented.
3. The API binds to `127.0.0.1` by default.
4. UUIDs are identifiers, not authorization.
5. Public or multi-user deployment is unsupported and requires a new milestone
   with authentication, CSRF/session handling, upload quotas, and audit rules.

## Rationale

- MIT keeps the project reusable and commercially viable.
- The NC restriction attaches to `stum`, not to independent code that invokes a
  separately installed binary.
- Adding half-built auth would be worse than an explicit single-user boundary.
- The brief does not require multi-user operation.

## Consequences

- "Job ownership" is out of scope until authentication exists.
- Security documentation must state the local-only boundary prominently.
- Any future public deployment is a breaking security change, not a config
  toggle.
