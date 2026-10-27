# BACKLOG.md

Deferred ideas and out-of-scope work. **Nothing here may be implemented
without explicit approval** and a milestone entry in `PLAN.md`.

## Deferred technical improvements

| ID | Item | Why deferred | Revisit |
|---|---|---|---|
| B-001 | Object-storage adapter (S3-compatible) | Local filesystem is sufficient for v1 | After M7 |
| B-002 | Redis/Celery queue | DB-backed queue avoids an extra service | Only if throughput demands it |
| B-003 | Authentication and multi-user tenancy | v1 is a single-user local tool | Before any public deployment |
| B-004 | Media deletion and retention automation | Needs a product policy and audit rules | After M7 |
| B-005 | Resumable uploads | Large-file UX, complexity | After M2 |
| B-006 | Background export queue | Exports are fast for short films | If large tracks block requests |
| B-007 | Advanced detector (scene-change + ML text detection) | Native heuristic must ship first | After M4 evaluation |
| B-008 | OCR language packs beyond English | Requires representative test corpus | Per language |
| B-009 | Vertical/mirrored intertitle correction | `stum` notes mirrored cards; native detector may need it | During M4 |
| B-010 | Speaker/character attribution | Explicitly out of scope | Not planned |
| B-011 | Frame-accurate VFR fixture in CI | Heavier test matrix | M4 |
| B-012 | Metrics/tracing | Single-node tool | After M7 |
| B-013 | Internationalized UI | Product is English-first | Future |
| B-014 | Subtitle style/position metadata | SRT/VTT v1 is text-only | Future |
| B-015 | Persist detection results and expose them over HTTP | M1 deliberately ships only `media_assets` and `processing_jobs`; M4 core currently runs via CLI | M2/M4 |
| B-016 | Intertitle review UI for detected candidates | Needs upload, persistence, and the M5 editor | M5 |
| B-017 | Watermelon UI registry block adoption | Reviewed blocks (`announcement-1`, `badge-15`, `alert-16`, dashboards) contained fake content, Base UI primitives, or arbitrary colours; none fit the archival workstation | Revisit when a block is genuinely useful |
| B-018 | Real-film OCR corpus and accuracy measurement | Only the synthetic fixture is tested; no accuracy claim is made | After M4 persistence |

## Explicitly out of scope (initial release)

- Machine translation.
- AI narration, TTS, voice acting, dubbing.
- Lip synchronisation.
- Character identification.
- Public archives, social feeds, sharing.
- Payments, subscriptions, monetisation.
- Multi-tenant enterprise features.
- Training custom ML models.
- Burned-in subtitles or video re-encoding.
- Any feature that does not serve the core extract → review → export workflow.

## Design extension points (interfaces only, no implementation)

- `TranslationProvider` for future translation.
- `DialogueStyler` for expressive dialogue generation.
- `OcrEngine` for additional OCR engines.
- `StorageBackend` for object storage.
- `SubtitleSerializer` for additional formats.

Interfaces are added only when a real implementation is scheduled. No empty
placeholder modules.

## Ideas parked by the human owner

Add entries here with date, requester, and rationale. Do not promote an entry
to `PLAN.md` without approval.
