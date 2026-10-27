# API.md

Status: **design contract for M1–M7. No endpoint is implemented yet.** The
generated OpenAPI document is authoritative once implementation exists; this
file is updated in the same change as any contract change.

## 1. Conventions

- Base path: `/api/v1`.
- Content type: `application/json` except uploads (multipart) and downloads.
- Resource identifiers: UUID strings.
- Media positions: integer microseconds in JSON, suffixed `_us`.
- Instants: ISO 8601 UTC with `Z`.
- Unknown fields in request bodies are rejected (`422`).
- All responses include `X-Request-ID`.
- OpenAPI is served at `/api/v1/openapi.json`; the frontend consumes generated
  types.

## 2. Error envelope

```json
{
  "error": {
    "code": "entry_overlap",
    "message": "Subtitle entry overlaps the previous entry.",
    "details": [
      { "field": "start_us", "reason": "must be greater than or equal to 1250000" }
    ],
    "request_id": "8f0c2b1e-7a1d-4a6b-9d3f-2f0f6a1c9d10"
  }
}
```

Rules:

- `message` is safe for users: no stack traces, no absolute paths, no SQL.
- `code` is stable and documented; the frontend may branch on it.
- Validation failures use `422`; malformed JSON uses `400`; unsupported media
  uses `415`; too large uses `413`; missing resources use `404`; conflicts use
  `409`; rate limiting, if added, uses `429`.

| Code | HTTP | Meaning |
|---|---|---|
| `validation_error` | 422 | Request schema or field invalid |
| `upload_too_large` | 413 | Exceeds configured limit |
| `unsupported_media` | 415 | Extension/content not allowed |
| `invalid_media` | 422 | ffprobe cannot read a usable video stream |
| `not_found` | 404 | Unknown resource |
| `job_conflict` | 409 | Active job already exists for media |
| `invalid_transition` | 409 | State change not allowed |
| `entry_overlap` | 422 | Subtitle timing overlap |
| `export_invalid` | 422 | Track cannot produce a valid file |
| `stum_unavailable` | 409 | `stum` requested but not installed/enabled |
| `internal_error` | 500 | Unexpected failure (no internals leaked) |

## 3. Resources

### 3.1 Health

`GET /api/v1/health` → `200`

```json
{ "status": "ok", "version": "0.1.0" }
```

Liveness only; does not touch dependencies.

`GET /api/v1/health/ready` → `200` when the database is reachable, `503`
otherwise.

```json
{ "status": "ready", "database": "ok" }
```

### 3.2 Media

#### `POST /api/v1/media`

Multipart form, single field `file`. Server enforces:

- configured maximum size (`MAX_UPLOAD_BYTES`),
- extension allowlist,
- actual container/stream validation via ffprobe,
- server-generated storage name,
- SHA-256 of the received bytes.

Response `201`:

```json
{
  "id": "2b7c1f4e-7d3a-4c1e-9b0f-1a2c3d4e5f60",
  "original_filename": "nosferatu_1922.mp4",
  "content_type": "video/mp4",
  "byte_size": 734003200,
  "sha256": "9f2c...",
  "duration_us": 5640000000,
  "width": 1920,
  "height": 1080,
  "frame_rate_num": 24000,
  "frame_rate_den": 1001,
  "time_base_num": 1,
  "time_base_den": 24000,
  "probe_status": "ok",
  "created_at": "2026-10-27T14:00:00Z"
}
```

Errors: `413`, `415`, `422` (`invalid_media`), `500`.

#### `GET /api/v1/media`

Query: `limit` (default 20, max 100), `cursor`, optional `probe_status`.

```json
{
  "items": [ { "...": "media object" } ],
  "next_cursor": "eyJjcmVhdGVkX2F0IjoiLi4uIiwiaWQiOiIuLi4ifQ"
}
```

#### `GET /api/v1/media/{media_id}`

Returns the media object or `404`.

#### `DELETE /api/v1/media/{media_id}`

Not in the initial API surface. Deferred to a deletion/retention decision in
`BACKLOG.md`.

### 3.3 Processing jobs

#### `POST /api/v1/media/{media_id}/jobs`

Header: `Idempotency-Key` (required).

```json
{
  "detector": "native",
  "ocr_language": "eng",
  "options": {}
}
```

- `detector`: `"native"` (default) or `"stum"`.
- `ocr_language`: Tesseract language code, default `"eng"`. Only languages
  actually installed and tested are accepted; unknown codes return `422`.
- `options`: detector-specific, validated against a typed schema.

Response `202`:

```json
{
  "id": "c1a2...",
  "media_id": "2b7c...",
  "state": "queued",
  "stage": null,
  "progress": 0,
  "attempt": 0,
  "error": null,
  "created_at": "2026-10-27T14:01:00Z",
  "started_at": null,
  "completed_at": null
}
```

`Location: /api/v1/jobs/{id}`.

Behaviour:

- Same `Idempotency-Key` + same media returns the existing job (`200` or
  `202` with the same body; `202` is used consistently).
- A different key while an active job exists returns `409 job_conflict`.
- Requesting `stum` when `STUM_ENABLED=false` or the binary is absent returns
  `409 stum_unavailable`.

#### `GET /api/v1/jobs/{job_id}`

Returns the job object. Polling interval guidance: 1 s while active, back off
to 5 s after 30 s.

#### `POST /api/v1/jobs/{job_id}/cancel`

Requests cooperative cancellation. `202` in active states; `409
invalid_transition` if terminal. Idempotent for an already-cancelling job.

#### State transitions

```text
queued → validating → detecting → ocr_processing → review_required → completed
   │          │            │             │                │
   └──────────┴────────────┴─────────────┴────────────────┴──→ cancelled
                │            │             │
                └────────────┴─────────────┴──→ failed
failed → queued   (recoverable, attempts remaining)
```

`completed` is only reachable after a validated export artifact exists.

### 3.4 Intertitles

#### `GET /api/v1/media/{media_id}/intertitles`

Query: `limit` (default 100, max 500), `cursor`, optional `review_status`.

```json
{
  "items": [
    {
      "id": "d4e5...",
      "media_id": "2b7c...",
      "job_id": "c1a2...",
      "start_us": 12500000,
      "end_us": 15200000,
      "text": "The next morning…",
      "ocr_confidence": 0.9231,
      "detector": "native",
      "review_status": "machine",
      "created_at": "2026-10-27T14:05:00Z"
    }
  ],
  "next_cursor": null
}
```

#### `PATCH /api/v1/intertitles/{intertitle_id}`

Limited to review metadata. Text and timings are **not** editable here; use
subtitle entries.

```json
{ "review_status": "rejected" }
```

Allowed values: `machine`, `reviewed`, `rejected`.

### 3.5 Subtitle tracks and entries

#### `GET /api/v1/media/{media_id}/subtitle-tracks`

Returns all tracks for the media.

#### `POST /api/v1/media/{media_id}/subtitle-tracks`

```json
{
  "name": "English (OCR)",
  "language_tag": "en",
  "source": "ocr",
  "from_job_id": "c1a2..."
}
```

- `from_job_id` is optional; when present, entries are seeded from that job's
  intertitles in one transaction.
- Returns `201` with the track and a summary (`entry_count`).
- `409` if a track with the same name exists for the media.

#### `GET /api/v1/subtitle-tracks/{track_id}`

Returns track metadata plus a paginated entry list via
`GET /api/v1/subtitle-tracks/{track_id}/entries` (query: `limit`, `cursor`).

#### `POST /api/v1/subtitle-tracks/{track_id}/entries`

```json
{
  "start_us": 3000000,
  "end_us": 5200000,
  "text": "A new text card",
  "after_entry_id": null
}
```

- `sequence` is assigned server-side; `after_entry_id` (optional) inserts after
  that entry and renumbers transactionally.
- Rejects overlaps with `422 entry_overlap`.
- Returns `201`.

#### `PATCH /api/v1/subtitle-entries/{entry_id}`

```json
{
  "start_us": 3000000,
  "end_us": 5200000,
  "text": "Corrected text",
  "review_status": "reviewed"
}
```

- Partial update; omitted fields unchanged.
- `If-Match` is not used in v1; stale-write detection uses `updated_at`
  optimistic checking via an optional `expected_updated_at` field (M5
  decision). Until then, last write wins within a single-user deployment.
- Returns `200` with the entry.
- `422` for `end_us <= start_us`, overlap, empty text, or invalid values.

#### `DELETE /api/v1/subtitle-entries/{entry_id}`

`204`. Renumbers subsequent entries transactionally.

#### `POST /api/v1/subtitle-tracks/{track_id}/reorder`

```json
{ "entry_ids": ["id1", "id2", "id3"] }
```

Must contain every entry exactly once. Applies sequence updates in one
deferred-constraint transaction. `422` on mismatch.

### 3.6 Export

#### `POST /api/v1/subtitle-tracks/{track_id}/exports`

```json
{ "format": "srt" }
```

`format`: `srt` or `vtt`.

Behaviour:

1. Load entries in sequence order.
2. Validate non-empty, positive durations, no overlaps, valid Unicode.
3. Serialize.
4. Write to storage, compute SHA-256 and entry count.
5. Re-parse the generated file to validate it.
6. Persist `ExportArtifact` with `validation_status`.

Returns `201`:

```json
{
  "id": "e7f8...",
  "track_id": "a1b2...",
  "format": "srt",
  "entry_count": 42,
  "byte_size": 3120,
  "sha256": "…",
  "validation_status": "valid",
  "created_at": "2026-10-27T14:20:00Z",
  "download_url": "/api/v1/exports/e7f8.../download"
}
```

Invalid tracks return `422 export_invalid` with a list of problems; no file is
published.

#### `GET /api/v1/exports/{export_id}/download`

Returns the file with:

- SRT: `application/x-subrip; charset=utf-8`
- VTT: `text/vtt; charset=utf-8`
- `Content-Disposition: attachment; filename="<sanitized track name>.<ext>"`

No path from the client is used to locate the file. Only `validation_status =
valid` artifacts are downloadable.

**Design deviation:** the suggested
`GET /subtitle-tracks/{id}/export?format=srt` is replaced by the
create-then-download flow so that every downloadable file has a validated
artifact record and a checksum. This is recorded in ADR-0004.

## 4. Pagination

Cursor-based, opaque base64 cursor containing `(created_at, id)`.

```json
{ "items": [], "next_cursor": null }
```

Invalid cursors return `400 invalid_cursor`.

## 5. Concurrency and idempotency

- Job creation: `Idempotency-Key` plus the active-job partial unique index.
- Entry reordering: deferred unique constraint in one transaction.
- Export: identical content produces a deduplicated artifact (same
  `track_id`, `format`, `sha256`).
- Single-user deployment means no cross-user authorization checks; this is a
  documented boundary, not a security claim.

## 6. Versioning

- `/api/v1` is frozen once M1 ships; breaking changes require `/api/v2`.
- Additive fields are allowed in v1.
- Deprecations are announced in `CHANGELOG.md` and the OpenAPI description.

## 7. OpenAPI

- FastAPI generates `/api/v1/openapi.json`.
- CI fails if the committed generated TypeScript types differ from the schema.
- Request/response examples in this file must match the generated models.
