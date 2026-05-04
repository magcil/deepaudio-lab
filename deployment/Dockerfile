FROM python:3.12-slim

ARG SAMPLE_RATE=32000
ARG SEGMENT_DURATION=3.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SAMPLE_RATE=${SAMPLE_RATE} \
    SEGMENT_DURATION=${SEGMENT_DURATION}

WORKDIR /app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY deployment/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY deployment /app/deployment

EXPOSE 8000

CMD ["uvicorn", "deployment.main:app", "--host", "0.0.0.0", "--port", "8000"]
