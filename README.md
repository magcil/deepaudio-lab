# deepaudio-lab

DeepAudio-Lab: A simple app for easily prototyping deep learning models for audio related tasks.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js & npm
- [Docker](https://docs.docker.com/get-docker/)

---

## Running with Docker

Deployment compose files live under [`deploy/`](deploy/) — a **ports-less base**
plus per-environment overlays — and a root `Makefile` wraps the (otherwise long)
`docker compose` invocations.

```
deploy/
  docker-compose.base.yml    # all services, no published ports (shared)
  docker-compose.local.yml   # local overlay: publishes ports
  docker-compose.dev.yml     # dev-server overlay
  docker-compose.gpu.yml     # GPU overlay (composes onto any env)
  docker-compose.prod.yml    # standalone production (edge proxy, secrets)
  env/
    local.env                # local config (committed)
    dev.env                  # dev-server config (committed)
    prod.env.example         # production template → copy to prod.env (secret, gitignored)
```

### Environment

Local and dev configs are committed under `deploy/env/`, so the Make targets work
out of the box. For production, copy the template and fill in real secrets:

```bash
cp deploy/env/prod.env.example deploy/env/prod.env   # then edit; never commit it
```

### Common commands

| Command | What it runs |
|---|---|
| `make infra` | Local **infra only** (Postgres, SeaweedFS, Keycloak, Redis) — run backend/frontend on the host |
| `make up` | Local full app (CPU) |
| `make up-gpu` | Local full app with NVIDIA GPU |
| `make down` | Stop the local stack |
| `make dev` | Dev-server full app |
| `make prod` / `make prod-gpu` | Production (standalone), optionally with GPU |
| `make config-local` / `make config-prod` | Print the merged, resolved config (validation) |

GPU targets require `nvidia-container-toolkit` on the host.

<details><summary>Equivalent raw <code>docker compose</code> commands</summary>

Always run from the repo root with `--project-directory .` so the files in
`deploy/` resolve their relative paths (build contexts, mounts) against the repo
root:

```bash
# local full app (CPU)
docker compose --project-directory . \
  -f deploy/docker-compose.base.yml -f deploy/docker-compose.local.yml \
  --env-file deploy/env/local.env --profile app up -d --build

# add GPU (compose the gpu overlay on top)
docker compose --project-directory . \
  -f deploy/docker-compose.base.yml -f deploy/docker-compose.local.yml \
  -f deploy/docker-compose.gpu.yml \
  --env-file deploy/env/local.env --profile app up -d --build

# production (standalone — not a base+overlay)
docker compose --project-directory . -f deploy/docker-compose.prod.yml \
  --env-file deploy/env/prod.env up -d --build
```

</details>

### Background services & limits

The `app` profile also starts two maintenance services:

- **`beat`** — a Celery Beat scheduler that triggers the periodic reaper.
- **`maintenance-worker`** — a lean (no-GPU, no-PyTorch) Celery worker that runs
  the reaper on its own `maintenance` queue, so it never competes with training.

On each run (every `REAPER_INTERVAL_SECONDS`) the reaper:

1. Marks runs stuck **In Progress** whose worker died (expired liveness
   heartbeat) as **Failed**.
2. If `DATASET_RETENTION_ENABLED=true`, deletes datasets older than
   `DATASET_RETENTION_SECONDS` that are **not in use** by an active job.

Concurrency caps reject new jobs (HTTP 429/503) when a user or the system is at
its in-flight limit. The relevant `.env` knobs (full list in `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `MAX_USER_TRAININGS` / `MAX_SYSTEM_TRAININGS` | training caps (user / system) | 1 / 4 |
| `MAX_USER_EVALUATIONS` / `MAX_SYSTEM_EVALUATIONS` | evaluation caps | 2 / 4 |
| `MAX_USER_JOBS` / `MAX_SYSTEM_JOBS` | overall in-flight caps | 2 / 4 |
| `HEARTBEAT_INTERVAL_SECONDS` / `JOB_HEARTBEAT_TTL_SECONDS` | job liveness heartbeat | 30 / 180 |
| `REAPER_INTERVAL_SECONDS` | how often the reaper runs | 300 |
| `DATASET_RETENTION_ENABLED` | enable dataset auto-deletion | false |
| `DATASET_RETENTION_SECONDS` | age threshold for deletion | 2592000 (30d) |

These are read at container startup, so apply a change by recreating the
affected service (no rebuild needed) — e.g.:

```bash
docker compose --project-directory . \
  -f deploy/docker-compose.base.yml -f deploy/docker-compose.local.yml \
  --env-file deploy/env/local.env --profile app up -d --force-recreate maintenance-worker
```

### Service URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Keycloak admin | http://localhost:8080 |
| SeaweedFS master | http://localhost:9333 |
| SeaweedFS filer | http://localhost:8888 |
| SeaweedFS S3 API | http://localhost:8333 |
| SeaweedFS admin UI | http://localhost:23646 |

---

## Local development (without containers)

Requires the infra services to be running first (`make infra`).

### Environment

Create a `.env` file inside `backend/`:

```
DATABASE_URL=postgresql://deepaudio:deepaudio@localhost:5432/deepaudio
S3_API=http://localhost:8333
SEAWEEDFS_FILER_URL=http://localhost:8888
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=secret
DATA_BUCKET=raw-audios
CHECKPOINTS_BUCKET=checkpoints
ARTIFACTS_BUCKET=artifacts
USER_SPACE_LIMIT=10737418240
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=deepaudiolab
KEYCLOAK_CLIENT_ID=deepaudiolab-backend
KEYCLOAK_CLIENT_SECRET=dev-secret
```

The training limits, concurrency caps, heartbeat, and reaper settings all have
sensible defaults (see [Background services & limits](#background-services--limits)),
so you only need to add them to `backend/.env` if you want to override them.

### Backend dependencies

The heavy ML stack (`deepaudio-x` → PyTorch/CUDA) is an optional `ml` extra, so
the API and training worker need it installed explicitly:

```bash
cd backend
uv sync --extra ml
```

> Only running the maintenance worker/reaper? Plain `uv sync` (without `--extra
> ml`) is enough — it has no PyTorch dependency.

### Frontend dependencies

```bash
cd frontend
npm install
```

### 1. Celery worker

Each worker imports only the task modules it needs via `--include` (the Celery
app no longer imports them eagerly, which keeps the maintenance worker
PyTorch-free):

```bash
cd backend
uv run celery -A worker.app.celery_app worker --loglevel=info --pool=solo \
  --include=worker.training,worker.evaluation,worker.deployment
```

For auto-reload on code changes, install `watchfiles` and run:

```bash
uv run watchfiles "celery -A worker.app.celery_app worker --loglevel=info --pool=solo --include=worker.training,worker.evaluation,worker.deployment" backend
```

### 2. Backend

```bash
cd backend
uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 3. Frontend

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. (Optional) Background reaper

Only needed if you want the periodic reaper (stale-run cleanup and dataset
retention) while developing locally. Run the scheduler and a maintenance worker
in two terminals:

```bash
cd backend
uv run celery -A worker.app.celery_app beat --loglevel=info
```

```bash
cd backend
uv run celery -A worker.app.celery_app worker --loglevel=info --pool=solo \
  --queues=maintenance --include=worker.maintenance
```

See [Background services & limits](#background-services--limits) for the env
variables that control it.

---

## Development

Install backend dev dependencies (includes `pytest`, `ruff`, and type stubs)
alongside the ML extra:

```bash
cd backend
uv sync --extra ml --group dev
```

Lint:

```bash
uv run ruff check .
```
