# SECURITY.md

## Supported versions

The project is pre-release. No version is supported for production use yet.
Security fixes will be applied to the latest release once releases begin.

| Version | Supported |
|---|---|
| `main` (pre-release) | Development only |
| Releases | None yet |

## Reporting a vulnerability

Do **not** open a public issue for a vulnerability involving:

- arbitrary file read/write or path traversal,
- command injection through media metadata or filenames,
- denial of service through crafted media,
- leakage of local paths, secrets, or uploaded media,
- dependency compromise.

Until a public repository and private advisory channel exist, report privately
to the repository owner. A `SECURITY` contact will be added when the repository
is published. This document will be updated rather than leaving a dead address.

Include: affected version/commit, reproduction steps, impact, and any suggested
fix. Do not include personal media or third-party copyrighted films.

## Security boundaries (v1)

- **Single-user, local-first.** The API binds to `127.0.0.1` by default. There
  is no authentication or authorization in v1. Exposing it to a network is not
  supported.
- **Uploaded media is untrusted.** It is validated, stored, probed, and
  decoded; it is never executed.
- **The server filesystem is trusted only inside `STORAGE_ROOT`.** All paths
  are server-generated and containment-checked.
- **The database is trusted.** Credentials come from the environment.
- **The browser is untrusted.** OCR text is rendered as text, never HTML.
- **External binaries are trusted by installation, not by input.** FFmpeg,
  ffprobe, Tesseract, and optional `stum` are invoked with argument arrays,
  timeouts, and resource limits.

## Upload controls

- Configurable maximum size, enforced while streaming (not after buffering).
- Extension allowlist plus actual ffprobe inspection; extension alone is never
  sufficient.
- Reject empty files, non-video containers, and files without a video stream.
- Server-generated storage keys: `uploads/{uuid}/original{ext}`.
- Client filenames are sanitized for display only; no path separators, control
  characters, or reserved names.
- SHA-256 recorded for integrity and deduplication.
- Uploaded files are never served directly by the API; downloads are explicit
  endpoints with content-type and disposition controls.

## Process isolation

- `subprocess` with `list[str]` arguments, `shell=False`.
- Absolute binary paths from configuration where possible.
- Per-process timeout; kill process group on timeout or cancellation.
- Working directory inside the job's `work/` directory.
- Environment is minimised; no secrets passed to media tools.
- Concurrency limited to avoid memory exhaustion on small machines.
- Temporary files cleaned in `finally` blocks and by a startup sweep.

## Data handling

- Media is never uploaded to an external service.
- Logs exclude secrets, tokens, and absolute paths; media content is never
  logged.
- Error responses contain stable codes and safe messages only.
- Uploads are retained until explicit deletion. No automatic retention purge is
  implemented in v1.
- Backups are the operator's responsibility and must cover PostgreSQL and
  `uploads/`.

## Third-party risk

- `stum` is **CC-BY-NC 4.0**. It is optional, external, disabled by default,
  and never bundled. Enabling it makes that processing path non-commercial.
  See `THIRD_PARTY_NOTICES.md`.
- FFmpeg build licensing depends on compile flags. Verify `ffmpeg -version`
  before redistributing binaries; Ubuntu builds commonly enable GPL components.
- Dependencies are pinned and audited in CI.
- Model files are downloaded by operators, not committed or redistributed.

## Out of scope for v1

- Multi-user authentication, roles, or tenancy.
- Public internet exposure.
- Malware analysis of uploads beyond safe decoding.
- Encryption at rest (delegated to the host/volume).
- Compliance certifications.

## Disclosure policy

- Acknowledge reports within a reasonable time.
- Provide a remediation plan and credit unless anonymity is requested.
- Do not discuss an unresolved vulnerability publicly before a fix is
  available.
