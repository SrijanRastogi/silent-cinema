---
name: Backend Contract
description: Implement or change FastAPI endpoints, Pydantic schemas, SQLAlchemy models, Alembic migrations, job state transitions, and stable error codes consistently with the documented contract.
---

# Backend Contract

Use for API, schema, persistence, or job-state work.

## Read first

- `API.md`
- `DATABASE.md`
- `ARCHITECTURE.md` §4 (state machine)
- the relevant ADR

## Rules

### API

- Versioned under `/api/v1`.
- Request and response models are typed Pydantic models; unknown fields
  rejected.
- Consistent error envelope:
  `{"error": {"code","message","details","request_id"}}`.
- Stable codes documented in `API.md`; do not invent one without documenting it.
- No stack traces, SQL, or absolute paths in responses.
- Pagination for collections; cursor-based.
- `Idempotency-Key` for job creation.
- OpenAPI is generated; committed frontend types must match. CI enforces this.

### Persistence

- SQLAlchemy 2.x typed mappings.
- Alembic is the only schema mechanism; no `create_all()` in production.
- Every migration has a working `downgrade()`; test up and down.
- Explicit foreign keys, check constraints, and indexes.
- UUID public IDs; UTC timestamps; `*_us` integer microseconds.
- Transactions around multi-row invariants (reorder, export, job claim).

### Jobs

- Enforce the documented transition graph in the service layer.
- Reject invalid transitions with `409 invalid_transition`.
- Retry only recoverable errors, bounded by `max_attempts`.
- Claim with `FOR UPDATE SKIP LOCKED`; never double-process.
- `completed` only after validated output exists.

### Errors

- Map domain errors to HTTP status and safe messages in one place.
- Log the internal cause with correlation IDs; return the safe code.
- Do not leak user filenames or storage keys in errors.

## Tests

- Unit: schema validation, state transitions, error mapping.
- Integration: persistence, constraints, migrations up/down, idempotency,
  concurrency.
- Contract: OpenAPI diff.

## Prohibited

- Business logic in routes.
- Duplicated pipeline logic between API and worker.
- Automatic schema creation at startup.
- Breaking `/api/v1` without a version bump.
