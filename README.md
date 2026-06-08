# deepaudio-lab

DeepAudio-Lab: A simple app for easily prototyping deep learning models for audio related tasks.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js & npm
- [Docker](https://docs.docker.com/get-docker/)

---

## Running with Docker

### Environment

Copy the root `.env.example` to `.env` and adjust values if needed:

```bash
cp .env.example .env
```

The defaults work out of the box for local development.

### Infra only (recommended for active development)

Starts PostgreSQL, SeaweedFS, Keycloak, and Redis in containers while you run the backend and frontend locally:

```bash
docker compose up -d
```

To stop:

```bash
docker compose down
```

### Full app (all services containerised, no GPU)

Builds and starts every service including the backend, Celery worker, and frontend:

```bash
docker compose --profile app up --build
```

Pass `-d` to run in the background. To stop:

```bash
docker compose --profile app down
```

### Full app with GPU support

Required when the host machine has an NVIDIA GPU and `nvidia-container-toolkit` installed. This enables CUDA acceleration in the Celery training worker:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml --profile app up --build
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

Requires the infra services to be running first (`docker compose up -d`).

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

### Backend dependencies

```bash
cd backend
uv sync
```

### Frontend dependencies

```bash
cd frontend
npm install
```

### 1. Celery worker

```bash
cd backend
uv run celery -A worker.app.celery_app worker --loglevel=info --pool=solo
```

For auto-reload on code changes, install `watchfiles` and run:

```bash
uv run watchfiles "celery -A worker.app.celery_app worker --loglevel=info --pool=solo" backend
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

---

## Development

Install backend dev dependencies (includes `pytest`, `ruff`, and type stubs):

```bash
cd backend
uv sync --group dev
```

Lint:

```bash
uv run ruff check .
```
