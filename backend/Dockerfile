# ---- builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

# Export locked deps via uv then install with pip for reproducible builds.
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && uv export --frozen --no-dev --no-hashes -o /tmp/requirements.txt \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["/venv/bin/uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
