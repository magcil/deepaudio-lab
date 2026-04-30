# deepaudio-lab

DeepAudio-Lab: A simple app for easily prototyping deep learning models for audio related tasks.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js & npm

## Backend

The backend is a FastAPI app managed with `uv`.

### Setup

```bash
cd backend
uv sync
```

### Run

```bash
cd backend
uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Development

Install with dev dependencies (includes `pytest` and `ruff`):

```bash
cd backend
uv sync --group dev
```

Run tests:

```bash
uv run pytest
```

Lint:

```bash
uv run ruff check .
```

## Local Development with Celery + Redis

Training jobs are handled asynchronously via Celery with Redis as the broker. For local development, run Redis in Docker (infrastructure only) and Celery + FastAPI as local processes so you benefit from hot-reload and direct debugger access.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)

### Start Redis

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

To stop it:

```bash
docker stop redis
```

### Run FastAPI + Celery

Open two terminals from the `backend` directory:

```bash
# Terminal 1 — FastAPI
cd backend
uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# Terminal 2 — Celery worker
cd backend
uv run celery -A worker.app worker --loglevel=info --pool=solo
```

> `--concurrency=1` ensures only one training job runs at a time, preventing CPU/GPU resource starvation.

For auto-reloading the Celery worker on code changes, install `watchfiles` and run:

```bash
uv run watchfiles "celery -A worker.app worker --loglevel=info --pool=solo" backend
```

## Frontend

The frontend is a React + Vite app.

### Setup

```bash
cd frontend
npm install
```

### Run

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.
