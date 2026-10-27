# ARCHITECTURE.md

Status: **design for M1–M7. No application code exists yet.** This document
describes intended boundaries; it is not evidence that any component runs.

## 1. Style

A **modular monolith** deployed as three processes:

1. `api` — FastAPI HTTP server.
2. `worker` — long-running job processor.
3. `web` — static React build served by Vite in development and by a static
   host/reverse proxy in production.

One Python package, one database, one filesystem storage root. No
microservices, message broker, or cloud dependency is required.

## 2. Component map

```text
apps/web (React)
    │  HTTP /api/v1 (JSON + multipart)
    ▼
apps/api (FastAPI)
    ├── routes/          request parsing, status codes, response models
    ├── services/        business rules, transactions, orchestration
    ├── persistence/     SQLAlchemy models, repositories, sessions
    ├── media/           probe, frame extraction, storage adapters
    ├── detection/       IntertitleDetector interface + implementations
    ├── ocr/             OCR interface + Tesseract/stum adapters
    ├── subtitles/       timecode math, SRT/VTT serializers, validators
    └── jobs/            state machine, queue claim/lease, cancellation
             │
             ├── PostgreSQL (authoritative state)
             └── filesystem storage (uploads / work / exports)

apps/worker
    └── claims jobs from PostgreSQL, runs the same services as the API
```

Rules:

- Routes do not contain business logic.
- Services do not depend on FastAPI request/response objects.
- The worker and API share services; no duplicated pipeline.
- Detection and OCR are interfaces. The pipeline never imports Tesseract or
  `stum` directly.
- The frontend consumes generated OpenAPI types; it does not hand-write
  contract types.

## 3. Processing pipeline

```text
Upload
  → input validation
  → media probing (ffprobe)
  → processing job creation
  → intertitle detection
  → OCR extraction
  → timestamp/result validation
  → review and correction
  → SRT / WebVTT export
  → browser preview and download
```

Each stage has a defined input, output, error code, and test strategy:

| Stage | Input | Output | Failure |
|---|---|---|---|
| Upload | multipart file | stored file + `MediaAsset` | `upload_*` codes, 4xx |
| Validation | stored file | accepted media | `unsupported_media`, `invalid_media`, `upload_too_large` |
| Probe | stored file | duration, dimensions, rate, timebase | `probe_failed` |
| Job creation | media id + config | `ProcessingJob` | `job_conflict`, 409 |
| Detection | frames + probe metadata | candidate intervals | `detection_failed` |
| OCR | candidate crops | text + confidence | `ocr_failed` |
| Result validation | detections | normalized intertitles + track | `result_invalid` |
| Review | track entries | edited entries | `entry_invalid`, 422 |
| Export | track | validated artifact | `export_invalid` |
| Preview | artifact + video | synchronized playback | client-side error state |

A required stage failure stops the job. It never silently continues with partial
output marked as success.

## 4. Job state machine

States: `queued`, `validating`, `detecting`, `ocr_processing`,
`review_required`, `completed`, `failed`, `cancelled`.

Allowed transitions:

```text
queued          → validating | cancelled
validating      → detecting | failed | cancelled
detecting       → ocr_processing | failed | cancelled
ocr_processing  → review_required | failed | cancelled
review_required → completed | cancelled
failed          → queued            (recoverable, attempts remaining)
completed       → (terminal)
cancelled       → (terminal)
```

Rules:

- Every transition is persisted with `updated_at` and a structured log event.
- Invalid transitions are rejected by the service layer, not just the UI.
- `completed` is set only after the export artifact validates.
- Retries increment `attempt`; maximum is configurable (default 3).
- Only recoverable error classes may be retried. Validation and unsupported
  format errors are permanent.
- A partial unique index prevents more than one active job per media asset
  (`queued`, `validating`, `detecting`, `ocr_processing`, `review_required`).

## 5. Queue and worker lifecycle

No Redis in v1. The database is the queue:

1. Worker claims one job:

   ```sql
   SELECT id FROM processing_jobs
   WHERE state = 'queued' AND run_after <= now()
   ORDER BY created_at
   FOR UPDATE SKIP LOCKED
   LIMIT 1;
   ```

2. Claim sets `claimed_by`, `lease_expires_at`, `started_at`, and moves to
   `validating` in the same transaction.
3. The worker renews its lease during long stages.
4. On crash, an expired lease returns the job to `queued` (recoverable) or
   `failed` after maximum attempts.
5. Graceful shutdown finishes the current checkpoint or releases the lease.
6. Cancellation is cooperative: the worker checks a cancellation flag between
   frames, OCR batches, and before persistence.

Idempotency:

- `POST /media/{id}/jobs` requires an `Idempotency-Key`; repeats return the
  existing job.
- Re-running a stage must not duplicate intertitles; the pipeline writes in a
  single transaction per attempt and replaces only that attempt's results.

## 6. Database interactions

- One transaction per request/job step where consistency matters.
- Repositories accept a session; no global sessions.
- Media blobs never enter PostgreSQL.
- Job progress and state are written by the worker; the API reads them.
- Exports are recorded as artifacts only after validation succeeds.

Schema details: `DATABASE.md`.

## 7. Storage layout

Root configured by `STORAGE_ROOT` (default `./data`):

```text
data/
├── uploads/{media_id}/original{ext}
├── work/{job_id}/frames/...
├── work/{job_id}/candidates/...
└── exports/{track_id}/{export_id}.{srt|vtt}
```

Rules:

- Keys are generated server-side; the client filename is metadata only.
- Every resolved path must remain inside the configured root (`realpath`
  containment check).
- Work directories are deleted on success, failure, and cancellation, and
  swept on worker startup for orphans.
- Exports are deterministic and regenerable from the database.
- No automatic upload to any external service.

A future object-storage adapter must implement the same interface and preserve
these invariants.

## 8. Frontend architecture

- Vite SPA, React 19, TypeScript strict.
- Routes: dashboard, upload, processing, review editor, export.
- TanStack Query for server state; polling for job status while active.
- React Hook Form + Zod for forms.
- shadcn/ui primitives; selected Watermelon UI registry blocks (MIT) copied in
  with attribution.
- API client generated from OpenAPI; runtime validation at boundaries where
  practical.
- No fake progress. Progress reflects backend `progress`/`state`.
- Error, empty, loading, and success states are required for every page.

Design system: `docs/UI.md`.

## 9. Failure handling

- Typed error codes mapped to HTTP status and safe messages.
- No stack traces or filesystem paths in responses.
- Structured logs include `request_id`, `job_id`, `media_id`; secrets and
  absolute paths are redacted.
- External processes have timeouts and are killed on cancellation.
- Temp cleanup runs in `finally` blocks and on startup sweeps.
- Partial outputs are never marked complete.

## 10. Security boundaries

| Boundary | Control |
|---|---|
| Browser → API | Size limits, content-type validation, loopback binding in dev |
| API → filesystem | Generated keys, path containment, no execution |
| API/worker → FFmpeg/Tesseract/stum | Argv arrays, timeouts, resource limits, no shell |
| API/worker → DB | Parameterized queries, least-privilege roles |
| Media → user | Untrusted content; no HTML rendering of OCR text without escaping |
| Operator | Single-user local deployment; no public multi-tenant claim |

No authentication is implemented in v1. This is a documented boundary, not an
oversight. Public deployment requires a separate approved milestone.

## 11. Extension points (not implemented)

- `TranslationProvider` interface for future machine translation.
- `DialogueStyler` interface for future expressive text generation.
- Additional OCR engines behind `OcrEngine`.
- Object storage behind `StorageBackend`.
- Additional subtitle formats behind `SubtitleSerializer`.

These are interfaces to design for, not code to add now. No placeholder
implementations in production paths.

## 12. Deployment topology

Development and single-node production:

```text
[web static build] → [reverse proxy] → [api] → [postgres]
                                          └──→ [worker] → [filesystem]
```

- Migrations run explicitly before startup, never automatically.
- API and worker share the storage root.
- Health endpoints: liveness and readiness.
- No paid cloud service required.

Details: `DEPLOYMENT.md`.
