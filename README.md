# deepaudio-lab

DeepAudio-Lab: A simple app for easily prototyping deep learning models for audio related tasks.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js & npm
- [Docker](https://docs.docker.com/get-docker/)

## Setup

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

### Environment

Create a `.env` file inside `backend/`:

```
DATABASE_URL=postgresql://deepaudio:deepaudio@localhost:5432/deepaudio
```

## Running the app

Start all services in the following order.

### 1. PostgreSQL + SeaweedFS for raw dataset storage

```bash
cd database
docker compose up -d
```

To stop:

```bash
docker compose down
```

The database tables are created automatically on first startup. Seaweedfs runs seaweedfs-mini to spin up four containers managing the microservices for:

1. Master UI: http://localhost:9333
2. Volume Server: http://localhost:9340
3. Filer UI: http://localhost:8888
4. WebDAV: http://localhost:7333
5. Admin UI: http://localhost:23646 

Upon start-up the seaweedfs will create two buckets:

1. `raw-audios`: This bucket contains the raw audio wav files uploaded by the Users
2. `checkpoints`: This bucket will be used to store the checkpoints.

### 2. Redis

```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

To stop:

```bash
docker stop redis
```

### 3. Celery worker

```bash
cd backend
uv run celery -A worker.app worker --loglevel=info --pool=solo
```

For auto-reload on code changes, install `watchfiles` and run:

```bash
uv run watchfiles "celery -A worker.app worker --loglevel=info --pool=solo" backend
```

### 4. Backend

```bash
cd backend
uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 5. Frontend

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.

## Development

Install backend dev dependencies (includes `pytest`, `ruff`, and type stubs):

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
