# ADR-0005 — Background processing and job state

- **Status:** Accepted (M0)
- **Date:** 2026-10-27

## Context

Video processing is long-running and must not block HTTP requests. A queue must
prevent duplicate processing, survive worker crashes, support cancellation, and
avoid unnecessary infrastructure on a single-node deployment.

## Decision

Use **PostgreSQL as the queue**, with a separate worker process and
`FOR UPDATE SKIP LOCKED` claiming. No Redis or Celery in v1.

1. Jobs live in `processing_jobs` with explicit states:
   `queued`, `validating`, `detecting`, `ocr_processing`, `review_required`,
   `completed`, `failed`, `cancelled`.
2. Workers claim with `SKIP LOCKED`, set `claimed_by` and `lease_expires_at`,
   and move to `validating` in the same transaction.
3. Long stages renew the lease. Expired leases are recovered on worker startup
   or by a periodic sweep.
4. Cancellation is cooperative and checked between frames, OCR batches, and
   before persistence.
5. Retries are allowed only for recoverable failures, up to `JOB_MAX_ATTEMPTS`
   (default 3). Validation and unsupported-format errors are permanent.
6. `POST /media/{id}/jobs` requires an `Idempotency-Key`; a partial unique index
   guarantees one active job per media.
7. `completed` is reachable only after validated export output exists.
8. Invalid transitions are rejected by the service layer and logged.

## Alternatives considered

- **Celery + Redis:** operationally heavier, adds a service and another failure
  mode, and is unnecessary at single-node scale.
- **FastAPI `BackgroundTasks`:** not durable; lost on restart; blocks the
  process under load.
- **Threads in the API process:** poor isolation for CPU-heavy FFmpeg/OpenCV
  work and no independent restart.

## Consequences

- The database must support row locking (PostgreSQL does).
- Queue throughput is sufficient for one operator; scaling out is possible by
  adding workers.
- Stale-lease recovery and idempotency become first-class tested behaviours.
- Redis remains a documented backlog option if throughput ever demands it.
