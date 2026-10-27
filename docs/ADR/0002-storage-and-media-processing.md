# ADR-0002 — Storage and media processing

- **Status:** Accepted (M0)
- **Date:** 2026-10-27

## Context

Uploaded films can be large, processing produces many temporary frames, and
exports are small but must be reproducible. The database must not store media
blobs. The system must not require a paid cloud service.

## Decision

1. Use a `StorageBackend` interface with a **local filesystem** adapter in v1.
2. Separate roots under `STORAGE_ROOT`:
   - `uploads/{media_id}/original{ext}`
   - `work/{job_id}/...`
   - `exports/{track_id}/{export_id}.{ext}`
3. Generate all storage keys server-side; client filenames are metadata only.
4. Validate paths with `realpath` containment before any read/write.
5. Use **FFmpeg/ffprobe via argument arrays**, never shell strings, with
   timeouts, a job-scoped working directory, and process-group termination.
6. Use exact rational `time_base` and frame rate from ffprobe. Convert frame
   timestamps with `pts × time_base`, never `frame_number / rounded_fps`.
7. Delete work directories on success, failure, and cancellation; sweep
   orphaned work directories on worker startup.
8. Uploaded media is retained until explicit deletion. Exports are
   regenerable; losing them is acceptable.
9. No external upload of user media.

## Alternatives considered

- **Store media in PostgreSQL:** rejected; bloats backups, poor streaming,
  violates the brief.
- **Object storage now:** rejected; adds credentials, cost, and a second
  failure domain before the core workflow works.
- **Frame-count timestamps:** rejected; wrong under variable frame rate and
  rounding.

## Consequences

- Single-node deployment only, sharing one filesystem between API and worker.
- Disk capacity is an operational concern; temporary frames can exceed the
  upload size.
- An object-storage adapter can be added later behind the same interface.
- FFmpeg build licensing must be checked before shipping binaries
  (see `THIRD_PARTY_NOTICES.md`).
