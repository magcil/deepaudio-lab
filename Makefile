# Deployment shortcuts. Every target runs from the repo root with
# `--project-directory .` so the compose files under deploy/ resolve their
# relative paths (build contexts, mounts) against the repo root.

COMPOSE := docker compose --project-directory .
BASE    := -f deploy/docker-compose.base.yml
GPU     := -f deploy/docker-compose.gpu.yml

LOCAL   := $(BASE) -f deploy/docker-compose.local.yml --env-file deploy/env/local.env
DEV     := $(BASE) -f deploy/docker-compose.dev.yml   --env-file deploy/env/dev.env
PROD    := -f deploy/docker-compose.prod.yml          --env-file deploy/env/prod.env

.PHONY: infra up up-gpu down dev dev-down prod prod-gpu prod-down config-local config-prod

## infra      — local infra only (Postgres, SeaweedFS, Keycloak, Redis); run backend/frontend on host
infra:
	$(COMPOSE) $(LOCAL) up -d

## up         — local full app (CPU)
up:
	$(COMPOSE) $(LOCAL) --profile app up -d --build

## up-gpu     — local full app with NVIDIA GPU
up-gpu:
	$(COMPOSE) $(LOCAL) $(GPU) --profile app up -d --build

## down       — stop the local stack
down:
	$(COMPOSE) $(LOCAL) --profile app down

## dev        — dev-server full app
dev:
	$(COMPOSE) $(DEV) --profile app up -d --build

## dev-down   — stop the dev stack
dev-down:
	$(COMPOSE) $(DEV) --profile app down

## prod       — production (standalone: edge proxy, secrets)
prod:
	$(COMPOSE) $(PROD) up -d --build

## prod-gpu   — production with NVIDIA GPU
prod-gpu:
	$(COMPOSE) $(PROD) $(GPU) up -d --build

## prod-down  — stop the production stack
prod-down:
	$(COMPOSE) $(PROD) down

## config-local / config-prod — print the merged, resolved config (validation)
config-local:
	$(COMPOSE) $(LOCAL) --profile app config

config-prod:
	$(COMPOSE) $(PROD) config
