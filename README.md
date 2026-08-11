# DeepAudioLab

<p align="left">
  <img src="DeepAudioLab-logo.png" style="width: 60%" alt="DeepAudioLab logo">
</p>

**A no-code platform for training, evaluating, and deploying audio classification models.**

DeepAudioLab lets you take a folder of audio recordings and turn it into a working, deployable audio classifier, with no code required. Upload your data, configure an experiment through a simple web UI, and DeepAudioLab handles training, evaluation, and packaging for deployment.

---

## Table of Contents

- [What is DeepAudioLab?](#what-is-deepaudiolab)
- [Key Features](#key-features)
- [How a Model Is Built](#how-a-model-is-built)
- [Quick Start](#quick-start)
- [Tuning Limits for Large-Scale Experiments](#tuning-limits-for-large-scale-experiments)
- [Deployment Reference](#deployment-reference)
  - [Compose Files & Make Targets](#compose-files--make-targets)
  - [Maintenance Services & Concurrency Caps](#maintenance-services--concurrency-caps)
  - [Service URLs](#service-urls)
- [Local Development](#local-development)
  - [Running Services on the Host](#running-services-on-the-host)
- [User Guide](#user-guide)
  - [1. Create an Account / Sign In](#1-create-an-account--sign-in)
  - [2. Prepare and Upload a Dataset](#2-prepare-and-upload-a-dataset)
  - [3. Train a Model](#3-train-a-model)
  - [4. Monitor Progress](#4-monitor-progress)
  - [5. Evaluate a Model](#5-evaluate-a-model)
  - [6. Deploy a Trained Model (Bundle)](#6-deploy-a-trained-model-bundle)

---

## What is DeepAudioLab?

DeepAudioLab is a web-based platform for training, evaluating, and deploying deep learning audio classifiers. Starting with a raw folder of `.wav` files, a user is able to produce a deployable, containerized model, with **zero code** and **no local GPU required**.

DeepAudioLab supports:
- Multiple pretrained backbone architectures (via the internal `deepaudio-x` library) (see [https://github.com/magcil/deepaudio-x](https://github.com/magcil/deepaudio-x))
- Near Real-time training progress tracking
- On-premises or private-cloud deployment, fully containerized with Docker Compose

## Key Features

| Feature | Description |
|---|---|
| 🎛️ No-code training | Configure an experiment via drop-down menus with no scripting required |
| 📊 Live monitoring | Near Real-time loss curves and an Activity Monitor for all running jobs |
| 🧪 Built-in evaluation | Per-class precision/recall/F1 classification reports |
| 📦 One-click deployment | Package any trained model into a self-contained, runnable inference bundle |
| 🔒 Secure by design | Keycloak-based auth, pre-signed storage URLs, HTTPS in production |

## How a Model Is Built

Every model trained in DeepAudioLab is assembled from three interchangeable pieces:

1. **Backbone:** a pretrained audio network that turns raw audio into a sequence of feature vectors over time.
2. **Pooling method:** aggregates those features along the time axis into a single compact summary of the clip.
3. **Linear classification head:** maps the pooled summary to your class predictions.

You pick the backbone and pooling method from drop-downs; DeepAudioLab assembles and trains the model for you.

## Quick Start

We recommend running the app via [docker](https://docs.docker.com/get-docker/). To install the app locally using only the CPU simply run the command

```bash
make up
```

This will start all microservices of the app (e.g., frontend, backend, worker, database, etc.). If nvidia GPU is available then run the command (requires the `nvidia-container-toolkit` to be installed on host)

```bash
make up-gpu
```

Once the app is installed navigate to the keycloak admin panel in [http://localhost:8080](http://localhost:8080) and login using the default admin credentials:

- username: `admin`
- password: `admin`

Select the deepaudiolab realm and create a user in `Users` section. Once the user is created you are ready to interact with app! Navigate to the frontend in [http://localhost:5173](http://localhost:5173) and enter your user credentials. 

Congrats! You are inside the web-app and ready to develop your audio classification systems!

For detailed instructions on how to interact with the UI you can check the [User Manual](docs/DeepAudioLab-user-manual.md).

---

## Tuning Limits for Large-Scale Experiments

The local stack is configured by [`deploy/env/local.env`](deploy/env/local.env). Its defaults are deliberately conservative so the app runs comfortably on a laptop. If you have a bigger machine (or a GPU) and want to run larger-scale experiments, these are the limits to raise:

| Variable | Default | What it caps |
|---|---|---|
| `USER_SPACE_LIMIT` | `10737418240` (10 GB) | Total upload quota **per user**. Exceeding it rejects the dataset upload. |
| `TOTAL_STORAGE_LIMIT` | `107374182400` (100 GB) | Upload quota **across all users**, a system-wide ceiling. |
| `MAX_SEGMENT_DURATION` | `10.0` | Longest audio segment, in seconds, allowed per training example. |
| `MAX_EPOCHS` | `100` | Highest number of epochs a training run may request. |
| `MAX_BATCH_SIZE` | `128` | Largest batch size accepted. Raise only as far as your GPU memory allows. |
| `MAX_NUM_WORKERS` | `4` | Most CPU data-loading workers per job. Keep at or below your core count. |

The two storage limits are in **bytes** (`107374182400` = 100 GB). The other four are ceilings checked when a job is submitted, so a run asking for more is rejected with a clear error rather than silently clamped.

**To apply a change,** edit the file and bring the stack back up:

```bash
make up
```

These values are read at container startup, so this recreates the backend with the new limits. No rebuild is needed, since only configuration changed.

> These limits govern how large a *single* job may be. The separate caps on *how many* jobs run concurrently are described in [Maintenance Services & Concurrency Caps](#maintenance-services--concurrency-caps).

`local.env` holds the rest of the local configuration as well, including database credentials, S3 bucket names, and the job concurrency, heartbeat, and dataset-retention settings. It is commented throughout, so it is worth a read before a large run.

---

## Deployment Reference

### Compose Files & Make Targets

Deployment compose files live under [`deploy/`](deploy/), a **ports-less base** plus per-environment overlays, and a root `Makefile` wraps the (otherwise long) `docker compose` invocations.

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

**Environment:** local and dev configs are committed under `deploy/env/`, so the Make targets work out of the box. For production, copy the template and fill in real secrets:

```bash
cp deploy/env/prod.env.example deploy/env/prod.env   # then edit; never commit it
```

**Common commands:**

| Command | What it runs |
|---|---|
| `make infra` | Local **infra only** (Postgres, SeaweedFS, Keycloak, Redis), run backend/frontend on the host |
| `make up` | Local full app (CPU) |
| `make up-gpu` | Local full app with NVIDIA GPU |
| `make down` | Stop the local stack |
| `make dev` | Dev-server full app |
| `make prod` / `make prod-gpu` | Production (standalone), optionally with GPU |
| `make config-local` / `make config-prod` | Print the merged, resolved config (validation) |

GPU targets require `nvidia-container-toolkit` on the host.

<details><summary>Equivalent raw <code>docker compose</code> commands</summary>

Always run from the repo root with `--project-directory .` so the files in `deploy/` resolve their relative paths (build contexts, mounts) against the repo root:

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

# production (standalone, not a base+overlay)
docker compose --project-directory . -f deploy/docker-compose.prod.yml \
  --env-file deploy/env/prod.env up -d --build
```

</details>

### Maintenance Services & Concurrency Caps

The `app` profile also starts two maintenance services:

- **`beat`:** a Celery Beat scheduler that triggers the periodic reaper.
- **`maintenance-worker`:** a lean (no-GPU, no-PyTorch) Celery worker that runs the reaper on its own `maintenance` queue, so it never competes with training.

On each run (every `REAPER_INTERVAL_SECONDS`) the reaper:

1. Marks runs stuck **In Progress** whose worker died (expired liveness heartbeat) as **Failed**.
2. If `DATASET_RETENTION_ENABLED=true`, deletes datasets older than `DATASET_RETENTION_SECONDS` that are **not in use** by an active job.

Concurrency caps reject new jobs (HTTP 429/503) when a user or the system is at its in-flight limit. The relevant `.env` knobs (full list in `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `MAX_USER_TRAININGS` / `MAX_SYSTEM_TRAININGS` | training caps (user / system) | 1 / 4 |
| `MAX_USER_EVALUATIONS` / `MAX_SYSTEM_EVALUATIONS` | evaluation caps | 2 / 4 |
| `MAX_USER_JOBS` / `MAX_SYSTEM_JOBS` | overall in-flight caps | 2 / 4 |
| `HEARTBEAT_INTERVAL_SECONDS` / `JOB_HEARTBEAT_TTL_SECONDS` | job liveness heartbeat | 30 / 180 |
| `REAPER_INTERVAL_SECONDS` | how often the reaper runs | 300 |
| `DATASET_RETENTION_ENABLED` | enable dataset auto-deletion | false |
| `DATASET_RETENTION_SECONDS` | age threshold for deletion | 2592000 (30d) |

These are read at container startup, so apply a change by recreating the affected service (no rebuild needed), e.g.:

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

## Local Development

### Running Services on the Host

Runs the backend, worker, and frontend directly on your machine instead of in containers. Requires the infra services to be running first (`make infra`).

**Environment** create a `.env` file inside `backend/`:

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
```

The backend only verifies JWTs against the realm's public JWKS, so it needs no Keycloak client id or secret, just the server URL and realm.

The training limits, concurrency caps, heartbeat, and reaper settings all have sensible defaults (see [Maintenance Services & Concurrency Caps](#maintenance-services--concurrency-caps)), so you only need to add them to `backend/.env` if you want to override them.

**Backend dependencies:** the heavy ML stack (`deepaudio-x` → PyTorch/CUDA) is an optional `ml` extra, so the API and training worker need it installed explicitly:

```bash
cd backend
uv sync --extra ml
```

> Only running the maintenance worker/reaper? Plain `uv sync` (without `--extra ml`) is enough, it has no PyTorch dependency.

**Frontend dependencies:**

```bash
cd frontend
npm install
```

**1. Celery worker:** each worker imports only the task modules it needs via `--include` (the Celery app no longer imports them eagerly, which keeps the maintenance worker PyTorch-free):

```bash
cd backend
uv run celery -A worker.app.celery_app worker --loglevel=info --pool=solo \
  --include=worker.training,worker.evaluation,worker.deployment
```

For auto-reload on code changes, install `watchfiles` and run:

```bash
uv run watchfiles "celery -A worker.app.celery_app worker --loglevel=info --pool=solo --include=worker.training,worker.evaluation,worker.deployment" backend
```

**2. Backend:**

```bash
cd backend
uv run uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`.

**3. Frontend:**

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.

**4. (Optional) Background reaper:** only needed if you want the periodic reaper (stale-run cleanup and dataset retention) while developing locally. Run the scheduler and a maintenance worker in two terminals:

```bash
cd backend
uv run celery -A worker.app.celery_app beat --loglevel=info
```

```bash
cd backend
uv run celery -A worker.app.celery_app worker --loglevel=info --pool=solo \
  --queues=maintenance --include=worker.maintenance
```

See [Maintenance Services & Concurrency Caps](#maintenance-services--concurrency-caps) for the env variables that control it.

---

## User Guide

For a detailed user guide please check the [User Manual](docs/DeepAudioLab-user-manual.md)

### 1. Create an Account / Sign In

Access is protected by Keycloak-based sign-in.

- **Register**: fill in username, password (+ confirmation), email, first and last name. All fields marked with a red asterisk are required.
- **Sign in**: enter your username or email and password. Optionally check **Remember me** to stay signed in on that device. Use **Forgot Password?** if needed.

Once signed in, you land on the **Homepage**, with a sidebar for navigation and your username/**Logout** button in the top-right corner.

The sidebar contains:

- **Homepage:** dashboard of your experiments
- **Training:** configure and start new training runs
- **Evaluation:** benchmark trained models against a test set
- **Datasets:** upload and manage audio datasets
- **Deployment:** package a trained model for use elsewhere
- **Activity Monitor:** track currently-running jobs

> **Recommended workflow order:** Datasets → Training → Evaluation → Deployment. You can click any tab at any time, but the app is designed around this flow.

### 2. Prepare and Upload a Dataset
Your dataset folder must follow this structure:

```
my_dataset/
├── train/
│   ├── class_1/
│   │   ├── audio_0001.wav
│   │   ├── audio_0002.wav
│   │   └── ...
│   ├── class_2/
│   │   └── ...
│   └── class_n/
│       └── ...
├── validation/
│   ├── class_1/
│   ├── class_2/
│   └── class_n/
└── test/
    ├── class_1/
    ├── class_2/
    └── class_n/
```

Rules:
- The top-level folder contains one sub-folder per **split** (e.g. `train`, `validation`, `test`). You choose later, during training, which sub-folder serves as which split.
- Inside each split folder there is one sub-folder per **class**, the folder name becomes the class label.
- Inside each class folder are the `.wav` files for that class.

**To upload:**
1. Open the **Datasets** tab and press **Upload Dataset**.
2. Give it a **Name** and optional **Description**, then press **Continue**.
3. Select the top-level dataset folder in your file browser and press **Upload**.

Once uploaded, the dataset appears as a card showing its name, description, total `.wav` file count, total size, and upload date. You only need to upload a dataset once and it can be reused across as many experiments as you like.

### 3. Train a Model

Open the **Training** tab. The page is organized into three tables, filled top to bottom.

**Data Configuration**
- **Experiment Name** and optional **Description**
- **Select Dataset:** choose from your uploaded datasets
- **Training Set** / **Validation Set:** pick the sub-folders for each split. Leaving Validation as `None` auto-holds-out 20% of training data (80/20 split).
- **Sampling Rate (Hz)** and **Segment Duration (s)**, e.g. 16000 Hz, 2-second segments

**Model Settings**
- **Backbone:** the pretrained feature extractor (see [Available Backbones](#available-backbones))
- **Pooling Method:** `gap`, `simpool`, or `ep` (see [Pooling Methods](#pooling-methods))
- **Pretrained:** start from pretrained weights (Yes) or from scratch (No)
- **Freeze Backbone:** train only the head (Yes) or the whole model (No)
- **Sampling Rate (Hz):** the rate the model itself operates at (audio is resampled if it differs from your data's rate)
- **Checkpoint:** a name for the saved `.pt` model file

**Hyperparameters**
- **Epochs**, **Patience** (early-stopping wait), **Learning Rate**, **Batch Size**
- **Workers** (1–8 CPU data-loading workers)
- **Device:** CPU, GPU (with index), or MPS (Apple Silicon)

Press **Start Training:** a green confirmation message appears, and the job starts running asynchronously.

### 4. Monitor Progress

Two complementary views:

- **Homepage experiment cards:** each card shows the run's name, description, and status (e.g. `TRAINING`). Click a card to open its **detail page**, which shows live train/validation loss curves (hover for exact values) and the full run configuration in a structured view.
- **Activity Monitor:** a live table of all running jobs (training, evaluation, deployment), each row showing status, start time, experiment name, job type, a progress bar, current/best validation loss, patience counter, elapsed time, and ETA.

> The Activity Monitor does not auto-refresh. Press **Refresh** to pull the latest state. Completed jobs disappear from this view; check the experiment's Homepage card for final results.

### 5. Evaluate a Model

1. Open the **Evaluation** tab.
2. Under **Choose Experiment**, select a model, only experiments that finished training are listed.
3. Set **Batch Size**, **Workers** (1–8), and **Device** (CPU/GPU/MPS).
4. Press **Run Evaluation**.

When finished, the experiment's card gains an `EVALUATED` tag. Open it to see the **classification report**: per-class **precision**, **recall**, **f1-score**, and **support**, plus overall **accuracy**, **macro average**, and **weighted average**.

### 6. Deploy a Trained Model (Bundle)

> This is about packaging a trained model for downstream use, not about deploying the DeepAudioLab application itself (see the [Deployment Reference](#deployment-reference) for that).

1. Open the **Deployment** tab.
2. Under **Create Bundle**, choose a trained (successful) **Experiment**.
3. Type a **Bundle Name** (e.g. `gtzan-classifier-v1`).
4. Press **Create Bundle**.

Building a bundle is a job. Thus, you can track it in the Activity Monitor.

Once complete, the bundle appears under **Available Bundles** with a **Download** button. A shortcut download icon also appears directly on the experiment's Homepage card.

**Running the bundle:** the downloaded ZIP is a self-contained inference package. Unzip it, build the included Docker image, and run the inference server locally or on any machine (full instructions are in the bundle's own README).

---