# DeepAudioLab

[![License](https://img.shields.io/github/license/magcil/deepaudio-x.svg)](https://github.com/magcil/deepaudio-lab/blob/main/LICENSE)
[![Run Tests](https://github.com/magcil/deepaudio-x/actions/workflows/tests.yml/badge.svg)](https://github.com/magcil/deepaudio-lab/actions/workflows/tests.yml)

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
- [Quick Start (Using the App)](#quick-start-using-the-app)
- [Installation & Running the App](#installation--running-the-app)
  - [Prerequisites](#prerequisites)
  - [Running with Docker](#running-with-docker)
  - [Background Services & Limits](#background-services--limits)
  - [Service URLs](#service-urls)
  - [Local Development (Without Containers)](#local-development-without-containers)
  - [Development & Testing](#development--testing)
- [User Guide](#user-guide)
  - [1. Create an Account / Sign In](#1-create-an-account--sign-in)
  - [2. Prepare and Upload a Dataset](#2-prepare-and-upload-a-dataset)
  - [3. Train a Model](#3-train-a-model)
  - [4. Monitor Progress](#4-monitor-progress)
  - [5. Evaluate a Model](#5-evaluate-a-model)
  - [6. Deploy a Trained Model (Bundle)](#6-deploy-a-trained-model-bundle)
- [Available Backbones](#available-backbones)
- [Pooling Methods](#pooling-methods)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Backend API](#backend-api)
- [Security](#security)
- [Data Storage Design](#data-storage-design)
- [Database Schema](#database-schema)
- [Glossary](#glossary)

---

## What is DeepAudioLab?

DeepAudioLab is a web-based platform for training, evaluating, and deploying deep learning audio classifiers. Starting with a raw folder of `.wav` files, a user is able to produce a deployable, containerized model, with **zero code** and **no local GPU required**.

DeepAudioLab supports:
- Multiple pretrained backbone architectures (via the internal `deepaudio-x` library)
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

## Quick Start (Using the App)

A condensed end-to-end checklist for a typical project, once the app is up and running (see [Installation & Running the App](#installation--running-the-app) below if you haven't set it up yet):

1. **Prepare your data** in the required folder structure (see [Prepare and Upload a Dataset](#2-prepare-and-upload-a-dataset)).
2. **Upload** the dataset on the **Datasets** tab.
3. **Train** a model on the **Training** tab: fill in Data Configuration, Model Settings, and Hyperparameters, then press **Start Training**.
4. **Monitor** the run via the Homepage experiment card and the **Activity Monitor**.
5. **Evaluate** the trained model on the **Evaluation** tab and read the classification report.
6. **Deploy** by creating a bundle on the **Deployment** tab, downloading it, and following the bundle's README.

---

## Installation & Running the App

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js & npm
- [Docker](https://docs.docker.com/get-docker/)

### Running with Docker

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

### Background Services & Limits

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

### Local Development (Without Containers)

Requires the infra services to be running first (`make infra`).

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

The training limits, concurrency caps, heartbeat, and reaper settings all have sensible defaults (see [Background Services & Limits](#background-services--limits)), so you only need to add them to `backend/.env` if you want to override them.

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

See [Background Services & Limits](#background-services--limits) for the env variables that control it.

### Development & Testing

Install backend dev dependencies (includes `pytest`, `ruff`, and type stubs) alongside the ML extra:

```bash
cd backend
uv sync --extra ml --group dev
```

Lint:

```bash
uv run ruff check .
```

---

## User Guide

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

> This is about packaging a trained model for downstream use, not about deploying the DeepAudioLab application itself (see [Installation & Running the App](#installation--running-the-app) for that).

1. Open the **Deployment** tab.
2. Under **Create Bundle**, choose a trained (successful) **Experiment**.
3. Type a **Bundle Name** (e.g. `gtzan-classifier-v1`).
4. Press **Create Bundle**.

Building a bundle is a job. Thus, you can track it in the Activity Monitor.

Once complete, the bundle appears under **Available Bundles** with a **Download** button. A shortcut download icon also appears directly on the experiment's Homepage card.

**Running the bundle:** the downloaded ZIP is a self-contained inference package. Unzip it, build the included Docker image, and run the inference server locally or on any machine (full instructions are in the bundle's own README).

---

## Available Backbones

| Backbone | Description | Reference |
|---|---|---|
| `beats` | Transformer-based audio model pre-trained self-supervised with acoustic tokenizers; strong general-purpose representations. | Chen et al., *BEATs: Audio Pre-Training with Acoustic Tokenizers*, ICML 2023 (arXiv:2212.09058) |
| `passt` | Patchout faSt Spectrogram Transformer: efficient audio transformer trained with patchout for speed and regularization. | Koutini et al., *Efficient Training of Audio Transformers with Patchout*, Interspeech 2022 (arXiv:2110.05069) |
| `mobilenet_05_as` | Efficient MobileNetV3-based CNN (0.5× width), pre-trained on AudioSet via knowledge distillation. Lightweight and fast. | Schmid et al., *Efficient Large-scale Audio Tagging via Transformer-to-CNN Knowledge Distillation*, ICASSP 2023 (arXiv:2211.04772) |
| `mobilenet_10_as` | Same efficient CNN at 1.0× width, balance of size and accuracy. | Schmid et al., ICASSP 2023 (arXiv:2211.04772) |
| `mobilenet_40_as` | Largest variant (4.0× width), highest accuracy, more compute. | Schmid et al., ICASSP 2023 (arXiv:2211.04772) |

## Pooling Methods

| Method | Description | Reference |
|---|---|---|
| `gap` | Global average pooling, averages features over the time axis. Simple and robust. | — |
| `simpool` | A simple attention-based pooling mechanism that learns how to combine features across time. | *Keep It SimPool: Who Said Supervised Transformers Suffer from Attention Deficit?* |
| `ep` | Efficient probing, attentive pooling designed for a good accuracy/efficiency trade-off. | *Attention, Please! Revisiting Attentive Probing Through the Lens of Efficiency* |

---

## Architecture Overview

DeepAudioLab is composed of containerized services communicating over a private Docker network:

- **Frontend SPA** (React 19 + Vite): the user-facing interface. Handles auth via Keycloak-JS (OIDC Authorization Code Flow with PKCE) before calling the Backend API.
- **Backend API** (FastAPI, Python 3.12): the central orchestrator. Validates JWTs on every request, manages dataset/run records in PostgreSQL, dispatches async ML tasks to the Celery Worker via Redis, and generates pre-signed S3 URLs for direct client-storage interaction.
- **Celery Worker** (Celery 5.3, Python 3.12): executes training, evaluation, and deployment jobs. Consumes tasks from Redis, writes loss metrics/status to PostgreSQL, and reads/writes model artifacts to object storage.
- **Redis**: Celery message broker and result backend; also holds live task progress state.
- **PostgreSQL**: all structured application data (users, datasets, runs, experiment parameters, loss history, classification reports).
- **SeaweedFS**: S3-compatible object storage for raw audio, checkpoints, and deployment artifacts, reachable by clients only via short-lived pre-signed URLs.
- **Keycloak**: identity and access management (registration, login, JWT issuance).

### Backend internal layering

The Backend API follows a strict layered architecture:

1. **Routers** (Auth, Dataset, Run, Training, Evaluation, Deployment, Task): REST entry points; handle routing, input validation, and response serialization only.
2. **Services** (Auth, Dataset, Run, Training, Evaluation, Deploy): all domain/business logic.
3. **Repositories** (User, Dataset, Run, Experiment Params, Loss, Classification Report): SQLAlchemy-based CRUD against PostgreSQL only.

No router talks directly to a repository, and no repository contains business logic. A JWT Verifier cuts across all layers, validating every inbound request against Keycloak's published public key before any handler executes.

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | React + TypeScript | 19.2 / 5.9 |
| Frontend Build Tool | Vite | 8.0 |
| UI Library | Bootstrap | 5.3 |
| Charts | Recharts | 3.8 |
| Backend | FastAPI + Uvicorn | 0.135 / 0.42 |
| ORM | SQLAlchemy | 2.0 |
| Task Queue | Celery + Redis | 5.3 / 7 |
| Database | PostgreSQL | 16 |
| Object Storage | SeaweedFS (S3-compatible) | 3.80 |
| Identity Provider | Keycloak | 26.0 |
| ML Framework | deepaudio-x, PyTorch | 0.4.6 |
| Container Runtime | Docker + Compose | latest |

## Backend API

All routes except the health check require a Bearer JWT issued by Keycloak, validated via RS256 signature. Long-running operations return `202 Accepted` with a `task_id` immediately, then run asynchronously.

| Domain | Method | Path | Auth | Description |
|---|---|---|---|---|
| root | GET | `/` | None | Health check |
| dataset | POST | `/datasets/presigned` | Regular | Enforce quota, register dataset, return per-file presigned upload URLs |
| dataset | POST | `/datasets/{id}/confirm` | Regular | Mark dataset ready; record size and file count |
| dataset | PATCH | `/datasets/{id}/error` | Regular | Mark dataset as errored after a failed upload |
| dataset | GET | `/datasets/` | Regular | List the authenticated user's datasets |
| dataset | GET | `/datasets/{id}/splits` | Regular | List split sub-directories for a dataset |
| dataset | DELETE | `/datasets/{id}` | Regular | Delete dataset record and all its S3 objects |
| train | POST | `/train/` | Regular | Start async training; creates Run + ExperimentParams |
| train | GET | `/train/options` | Regular | Available backbones, pooling strategies, device indices |
| train | GET | `/train/progress/{task_id}` | Regular | Epoch, losses, progress %, elapsed time, ETA |
| evaluate | GET | `/evaluate/options` | Regular | Available GPU/CPU device options |
| evaluate | POST | `/evaluate/` | Regular | Start async evaluation on the test split |
| evaluate | GET | `/evaluate/progress/{task_id}` | Regular | Evaluation progress and status |
| runs | GET | `/runs/` | Regular, Admin | List runs (own for regular users; all for admins) |
| runs | GET | `/runs/type/train` | Regular | List completed runs eligible for evaluation |
| runs | GET | `/runs/{id}` | Regular, Admin | Get run detail: params, loss history, report |
| runs | DELETE | `/runs/{id}` | Regular, Admin | Delete run record, checkpoint, and artifacts |
| runs | POST | `/runs/{id}/deploy` | Regular | Trigger async deployment bundle creation |
| runs | GET | `/runs/{id}/deploy/download` | Regular | Generate a fresh presigned bundle download URL |
| tasks | GET | `/tasks/` | Regular | List active tasks + failures from the last 24 hours |

## Security

- **Storage security**: object storage is never publicly reachable. All client interaction goes through Backend-issued, key-scoped pre-signed PUT/GET URLs.
- **Transport security**: all public traffic is HTTPS in production; internal service-to-service traffic stays on a private Docker bridge network. Keycloak is served on its own subdomain.
- **Secret management**: all credentials and keys are injected via environment variables / `.env` files at runtime and `.env` is git-ignored.

## Data Storage Design

Object storage (SeaweedFS, S3-compatible) is organized into three buckets:

| Bucket | Contents | Written by |
|---|---|---|
| `raw-audios` | Uploaded audio, as `{user_id}/{dataset_name}/{split}/{class}/{file}` | Browser (direct presigned PUT) |
| `checkpoints` | Best model weights (`.pt`) from training | Celery Worker |
| `artifacts` | Deployment bundle ZIPs | Celery Worker |

Client-side uploads go straight from the browser to storage via presigned URLs, keeping large binary payloads off the API tier. The expected `{split}/{class}/{file}.wav` structure is validated at training time. If it doesn't conform, the training task fails with a clear error.

**Asynchronous task state** is tracked in two tiers: coarse status (`pending`/`in_progress`/`failed`/`successful`) is persisted in PostgreSQL as the authoritative record; fine-grained progress (epoch, per-epoch loss, ETA) is written ephemerally to Redis during execution and polled on demand via `GET /train/progress/{task_id}`.

## Database Schema

Six core entities, with `Run` as the central table:

| Entity | Primary Key | Unique Constraint | Description |
|---|---|---|---|
| User | `id` (Keycloak UUID) | `username` | Registered user, mirrored from Keycloak |
| Dataset | `id` | `(user_id, name)` | Uploaded audio dataset; tracks status, S3 prefix, size, file count |
| Run | `id` | `(created_by, name)` | Central experiment entity, ties together config, loss history, and evaluation results |
| Experiment Params | `id` | `run_id` (1:1) | Full hyperparameter/config snapshot for a run |
| Loss | `id` | `(run_id, epoch, split_type)` | Per-epoch train/validation loss (many:1 with Run) |
| Classification Report | `id` | `run_id` (1:1) | Per-class precision/recall/F1 after evaluation |

A `User` owns zero-or-more `Dataset`s and `Run`s. Each `Run` has exactly one `ExperimentParams`, at most one `ClassificationReport`, and zero-or-more `Loss` records. All foreign keys cascade on delete. Names are unique per-user, not globally. `experiment_params.class_mapping` and `classification_report.report` are stored as JSON columns for schema flexibility.

## Glossary

| Term | Definition |
|---|---|
| Backbone | A pretrained neural network feature extractor used as the base of the audio classification model |
| Pooling | A strategy for aggregating temporal features into a fixed-size representation (e.g. Global Average Pooling) |
| Epoch | One complete pass through the entire training dataset |
| Patience | Number of epochs without validation-loss improvement before early stopping halts training |
| Presigned URL | A time-limited, pre-authenticated URL granting temporary permission for a specific S3 operation without API credentials |
| Celery | A distributed task queue framework for Python, delegating work to background workers via a message broker |
| SeaweedFS | An open-source, S3-compatible distributed object storage system |
| Keycloak | An open-source Identity and Access Management solution supporting OIDC, OAuth 2.0, and SAML 2.0 |
| OIDC | OpenID Connect, an identity layer on top of OAuth 2.0 providing JWT-based identity tokens |
| JWT | JSON Web Token, a compact, signed token encoding claims (RS256 here) |
| RBAC | Role-Based Access Control, permissions assigned to roles, not individual users |
| Classification Report | Summary of precision, recall, and F1-score per class, produced by `sklearn.metrics.classification_report` |
| Deployment Bundle | A ZIP archive containing model weights, class mapping JSON, and inference utilities, ready for integration |
| deepaudio-x | The custom internal PyTorch library used to construct and train audio classification models |
| C4 Model | A software architecture diagramming framework (Context, Containers, Components, Code) |

---