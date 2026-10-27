# DEPLOYMENT.md

Status: **design for M1+. Nothing is deployable yet.** Commands are the target
interface and must be verified before this document removes the "planned"
label.

## 1. Supported deployment

- Single-node Linux (x86_64) or macOS for development.
- Docker Compose for local parity.
- Native installation (Python + Node + system services) for development.
- No cloud service is required.
- Single-user, loopback-bound by default. Public multi-user deployment is out
  of scope and requires a separate security milestone.

## 2. Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.13 | API and worker |
| uv | current | Dependency and venv management |
| Node.js | 24 | Frontend build |
| npm | 11 | Frontend dependencies |
| PostgreSQL | 18 | Primary database |
| FFmpeg / ffprobe | 8.x | Media probing and frame extraction |
| Tesseract | 5.5+ | OCR |
| Docker + Compose | recent | Optional local parity |
| `stum` | optional, external | Optional detector adapter |

System packages on Ubuntu 26.04:

```bash
sudo apt-get update
sudo apt-get install -y \
  postgresql-18 python3.13 python3.13-venv \
  ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin \
  libpq-dev
```

Docker (optional):

```bash
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
# log out and back in
```

Tesseract language packs beyond English are installed explicitly and are not
claimed as supported until tested.

## 3. Environment variables

Copy `.env.example` to `.env`. Never commit `.env`.

| Variable | Default | Notes |
|---|---|---|
| `APP_ENV` | `development` | `development`, `test`, `production` |
| `APP_HOST` | `127.0.0.1` | Do not expose publicly by default |
| `APP_PORT` | `8000` | API port |
| `DATABASE_URL` | — | `postgresql+psycopg://user:pass@host:5432/db` |
| `STORAGE_ROOT` | `./data` | Uploads, work, exports |
| `MAX_UPLOAD_BYTES` | `2147483648` | 2 GiB default |
| `ALLOWED_VIDEO_EXTENSIONS` | `mp4,mkv,mov,avi,mpg,mpeg,webm` | Validated again by ffprobe |
| `FFMPEG_BIN` | `ffmpeg` | Absolute path recommended |
| `FFPROBE_BIN` | `ffprobe` | Absolute path recommended |
| `TESSERACT_BIN` | `tesseract` | Used by pytesseract |
| `OCR_DEFAULT_LANGUAGE` | `eng` | Must be installed |
| `WORKER_POLL_INTERVAL_SECONDS` | `2` | Queue polling |
| `WORKER_LEASE_SECONDS` | `120` | Lease renewal window |
| `JOB_MAX_ATTEMPTS` | `3` | Recoverable retries |
| `PROCESS_TIMEOUT_SECONDS` | `900` | Per external process |
| `STUM_ENABLED` | `false` | Optional adapter |
| `STUM_BIN` | `stum` | External binary |
| `LOG_LEVEL` | `info` | Structured logs |

Secrets belong in the environment or a secret manager, never in Git.

## 4. Database setup

```bash
sudo -u postgres psql -c "CREATE ROLE silent LOGIN PASSWORD 'silent_dev';"
sudo -u postgres createdb -O silent silent_cinema
```

Development only. Production uses a dedicated role with least privilege and a
managed password.

Migrations are explicit:

```bash
uv run alembic upgrade head
```

Never run migrations automatically on application startup. Back up before
upgrading in any non-disposable environment:

```bash
pg_dump --format=custom --file=backup.dump "$DATABASE_URL"
```

Rollback:

```bash
uv run alembic downgrade -1
```

Migrations that drop data must document the loss and require an explicit
decision.

## 5. Local development

```bash
cp .env.example .env
make doctor          # verifies binaries and versions
make bootstrap       # uv sync + npm ci
make migrate
make dev             # API + Vite dev server (worker is not started)
```

`make dev` runs the API and the web dev server. The worker placeholder exits
with an explicit message in M1 because there is no queue yet.

Expected services:

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`
- PostgreSQL: `127.0.0.1:5432`

The worker is a separate process. Starting the API alone does not process jobs;
the UI must report that honestly if no worker is running.

## 6. Docker Compose

Intended services:

| Service | Image | Purpose |
|---|---|---|
| `db` | `postgres:18-alpine` | Database with named volume |
| `api` | `docker/api.Dockerfile` | HTTP API |
| `worker` | `docker/api.Dockerfile`, profile `worker` | Placeholder; exits in M1 |
| `web` | not containerised in M1 | Run `npm run dev` or `npm run preview` |

Rules:

- The compose file pins image tags; no `latest` in production profiles.
- API and worker mount the same storage volume.
- Migrations run as an explicit one-off command, not an entrypoint side effect.
- Health checks use `/api/v1/health` and `/api/v1/health/ready`.

```bash
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d api
docker compose ps
```

The worker profile is opt-in and currently refuses to start work:

```bash
docker compose --profile worker run --rm worker
```

## 7. Health checks and observability

- `GET /api/v1/health` — process liveness.
- `GET /api/v1/health/ready` — database reachability.
- Worker logs include `job_id`, `media_id`, `state`, and duration.
- No secrets, tokens, or absolute paths in logs.
- Logs are structured JSON in production, human-readable in development.

## 8. Storage

```text
data/
├── uploads/   original media (retained)
├── work/      temporary frames and crops (deleted)
└── exports/   generated subtitles (regenerable)
```

- `STORAGE_ROOT` must be writable by API and worker.
- Back up `uploads/` and PostgreSQL together; exports are regenerable.
- Work directories are cleaned on success, failure, and cancellation, plus a
  startup sweep.
- Disk space: a 2 GiB upload can require several GiB of temporary frames. Plan
  capacity accordingly and document limits.

## 9. Production assumptions

- Single node, single user, trusted network or localhost.
- HTTPS terminated by a reverse proxy if exposed beyond loopback.
- No authentication in v1; exposing the API publicly is not supported.
- Uploaded media is untrusted and never executed.
- The deployment has not been validated on this machine; treat every command
  above as **[PLANNED]** until a milestone records the actual output.

## 10. Upgrade procedure

1. Back up the database and `uploads/`.
2. Pull the release, install locked dependencies.
3. Run `alembic upgrade head`.
4. Start API and worker; verify readiness.
5. Run a smoke export from an existing track.
6. Record the result in `docs/STATUS.md` / release notes.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| `ffprobe not found` | `make doctor`, `FFPROBE_BIN` |
| Jobs stay `queued` | Is the worker running? `GET /jobs/{id}` |
| `stum_unavailable` | `STUM_ENABLED`, `STUM_BIN`, `pipx list` |
| OCR returns empty text | Language pack, crop quality, Tesseract version |
| Upload rejected | Size limit, extension allowlist, ffprobe output |
| Migration fails | PostgreSQL version, role privileges, extension `btree_gist` |
