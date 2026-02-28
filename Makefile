REGISTRY  ?= ghcr.io
ORG       ?= $(shell git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\)\/.*/\1/')
VERSION   ?= $(shell git rev-parse --short HEAD)
BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

BACKEND_IMAGE  := $(REGISTRY)/$(ORG)/pgo-auctions-backend
FRONTEND_IMAGE := $(REGISTRY)/$(ORG)/pgo-auctions-frontend

.PHONY: up dev down build push ci

## Start the production-like stack
up:
	docker compose up --build

## Start the development stack with hot-reload
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

## Stop all services
down:
	docker compose down

## Build one or both service images
## Usage: make build [SERVICE=backend|frontend] [VERSION=v1.0.0]
build:
ifeq ($(SERVICE),backend)
	docker build \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		-t $(BACKEND_IMAGE):$(VERSION) \
		-t $(BACKEND_IMAGE):latest \
		src/backend
else ifeq ($(SERVICE),frontend)
	docker build \
		--build-arg VERSION=$(VERSION) \
		-t $(FRONTEND_IMAGE):$(VERSION) \
		-t $(FRONTEND_IMAGE):latest \
		src/frontend
else
	docker build \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(BUILD_DATE) \
		-t $(BACKEND_IMAGE):$(VERSION) \
		-t $(BACKEND_IMAGE):latest \
		src/backend
	docker build \
		--build-arg VERSION=$(VERSION) \
		-t $(FRONTEND_IMAGE):$(VERSION) \
		-t $(FRONTEND_IMAGE):latest \
		src/frontend
endif

## Push images to GitHub Container Registry
## Prerequisite: docker login ghcr.io
## Usage: make push [SERVICE=backend|frontend] [VERSION=v1.0.0]
push:
ifeq ($(SERVICE),backend)
	docker push $(BACKEND_IMAGE):$(VERSION)
	docker push $(BACKEND_IMAGE):latest
else ifeq ($(SERVICE),frontend)
	docker push $(FRONTEND_IMAGE):$(VERSION)
	docker push $(FRONTEND_IMAGE):latest
else
	docker push $(BACKEND_IMAGE):$(VERSION)
	docker push $(BACKEND_IMAGE):latest
	docker push $(FRONTEND_IMAGE):$(VERSION)
	docker push $(FRONTEND_IMAGE):latest
endif

## Run all quality gates (lint, type check, tests) then build images
ci:
	cd src/backend && ruff check app/ && mypy app/ && python -m pytest tests/ -v
	cd src/frontend && npx eslint src/ && npx vue-tsc --noEmit && npx vitest run
	$(MAKE) build
