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
