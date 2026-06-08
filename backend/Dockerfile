# ---- builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

# ML_EXTRA controls whether the heavy ML stack (deepaudio-x → torch/CUDA/librosa)
# is installed. Default builds the full image (API / training worker); the lean
# maintenance worker and beat build with ML_EXTRA="".
ARG ML_EXTRA="--extra ml"

# Export locked deps via uv then install with pip for reproducible builds.
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && uv export --frozen --no-dev --no-hashes ${ML_EXTRA} -o /tmp/requirements.txt \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# libsndfile1 is only needed for audio decoding (librosa), i.e. the ML image.
# Lean builds pass RUNTIME_LIBS="" to skip it.
ARG RUNTIME_LIBS="libsndfile1"
RUN apt-get update \
    && if [ -n "$RUNTIME_LIBS" ]; then apt-get install --yes --no-install-recommends $RUNTIME_LIBS; fi \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["/venv/bin/uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
