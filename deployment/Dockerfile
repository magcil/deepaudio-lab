# ---- builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch + torchaudio first so pip won't pull CUDA wheels
# when deepaudio-x resolves its dependencies.
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir \
        torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cpu \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- runtime ----
FROM python:3.12-slim AS runtime

ARG SAMPLE_RATE=32000
ARG SEGMENT_DURATION=3.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SAMPLE_RATE=${SAMPLE_RATE} \
    SEGMENT_DURATION=${SEGMENT_DURATION} \
    PATH="/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

WORKDIR /app

# Copy bundle contents into a stable package name so relative imports work.
COPY . /app/deployment

EXPOSE 8000

CMD ["/venv/bin/uvicorn", "deployment.main:app", "--host", "0.0.0.0", "--port", "8000"]
