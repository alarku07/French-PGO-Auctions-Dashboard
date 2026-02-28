# Quickstart: Docker Setup

**Branch**: `001-docker-setup` | **Date**: 2026-02-28

---

## Prerequisites

- Docker Engine (v24+) or Docker Desktop installed
- `make` available (for convenience commands)
- No other local services needed

---

## 1. Configure Environment

Copy the environment template and fill in secrets:

```bash
cp .env.docker.example .env.docker
# Edit .env.docker — at minimum set POSTGRES_PASSWORD and POSTGRES_USER
```

---

## 2. Start the Development Stack (hot-reload)

```bash
make dev
# or: docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- Frontend: http://localhost (Vite dev server via nginx proxy)
- Backend API docs: http://localhost/api/docs
- Logs: `docker compose logs -f`

Source code changes in `src/backend/` and `src/frontend/src/` reflect immediately without restarting containers.

---

## 3. Start the Production-Like Stack

```bash
make up
# or: docker compose up --build
```

- Application: http://localhost
- Backend API docs: http://localhost/api/docs

---

## 4. Stop the Stack

```bash
make down
# or: docker compose down
```

Database data is preserved in the `postgres_data` Docker volume. To also remove the volume: `docker compose down -v`

---

## 5. Build and Push Images to Registry

```bash
# Login to GitHub Container Registry first
docker login ghcr.io

# Build both images and tag with git SHA
make build

# Push to registry (uses git SHA tag by default)
make push

# Build and push with a semantic version tag
make push VERSION=v1.0.0
```

---

## 6. Build a Single Service Image

```bash
# Backend only
make build SERVICE=backend VERSION=v1.0.0

# Frontend only
make build SERVICE=frontend VERSION=v1.0.0
```

---

## Common Operations

| Task | Command |
|------|---------|
| View logs (all services) | `docker compose logs -f` |
| View logs (one service) | `docker compose logs -f backend` |
| Run a one-off migration | `docker compose run --rm backend alembic upgrade head` |
| Open a psql shell | `docker compose exec postgres psql -U pgo -d pgo_auctions` |
| Rebuild a single service | `docker compose build backend` |
| Check service health | `docker compose ps` |

---

## Environment Variable Reference

See `.env.docker.example` for all required variables with descriptions.

Key variables for Docker (differ from local dev):

| Variable | Docker value | Local dev value |
|----------|-------------|----------------|
| `DATABASE_URL` | `postgresql+asyncpg://pgo:secret@postgres:5432/pgo_auctions` | `postgresql+asyncpg://user:pass@localhost:5432/pgo_auctions` |
| `CORS_ORIGINS` | `http://localhost` | `http://localhost:5173` |
| `HOST` | `0.0.0.0` | `0.0.0.0` |
