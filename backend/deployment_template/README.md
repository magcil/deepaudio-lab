# DeepAudio Lab — Inference Bundle

This bundle contains a self-contained audio classification inference server
built from your trained model. It runs as a FastAPI application inside a
Docker container.

## Requirements

- [Docker](https://docs.docker.com/get-docker/) installed and running on your machine.

## 1 — Unzip the bundle

```bash
unzip <your-bundle-name>.zip -d my_model
cd my_model
```

## 2 — Build the Docker image

```bash
docker build -t deepaudio-inference .
```

The build installs all Python dependencies and packages the model checkpoint
into the image. This takes 1–3 minutes on the first run (subsequent builds
are faster due to Docker layer caching).

## 3 — Run the inference server

```bash
docker run -d -p 8000:8000 deepaudio-inference
```

The server starts on `http://localhost:8000`. Verify it is healthy:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "ok", "model": "loaded: /app/deployment/pretrained_models/checkpoint.pt"}
```

## 4 — Run inference

Send a WAV, FLAC, or MP3 file to the `/inference/` endpoint:

```bash
curl -X POST http://localhost:8000/inference/ \
  -F "path=@/path/to/audio.wav"
```

### Optional parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `segment_duration` | float | model default | Duration (seconds) of each analysis segment |
| `sample_rate` | int | model default | Expected sample rate of the audio |

Example with explicit parameters:

```bash
curl -X POST http://localhost:8000/inference/ \
  -F "path=@/path/to/audio.wav" \
  -F "segment_duration=3.0" \
  -F "sample_rate=22050"
```

### Response

```json
{
  "result": {
    "predicted_class": "blues",
    "posteriors": {
      "blues": 0.82,
      "jazz": 0.11,
      "rock": 0.07
    }
  }
}
```

## Audio constraints

| Constraint | Value |
|---|---|
| Minimum duration | 1 second |
| Maximum duration | 5 minutes |
| Maximum segment duration | 10 seconds |
| Supported formats | `.wav`, `.flac`, `.mp3` |

## API docs

Interactive Swagger UI is available at `http://localhost:8000/docs` while the
container is running.
