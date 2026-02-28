# Research: Docker Containerization Setup

**Branch**: `001-docker-setup` | **Date**: 2026-02-28

---

## RES-001: Backend Base Image

**Decision**: `python:3.14-slim`

**Rationale**: The `asyncpg` async PostgreSQL driver requires C extensions compiled against glibc. Alpine Linux uses musl libc, which causes asyncpg compilation failures or requires source builds from scratch. `python:3.14-slim` (Debian-based) provides glibc compatibility and pre-compiled wheels work out of the box.

**Alternatives considered**:
- `python:3.14-alpine` — rejected: asyncpg glibc incompatibility, longer build times, no meaningful size advantage after accounting for build toolchain

---

## RES-002: Backend Multi-Stage Build

**Decision**: Two-stage Dockerfile — `builder` stage installs dependencies and compiles extensions; `runtime` stage copies only installed site-packages and source code.

**Rationale**: Reduces final image size by ~70% by excluding gcc, build-essential, and pip cache. Separates build-time dependencies from runtime.

**Stages**:
1. `builder` (`python:3.14-slim`): `apt install build-essential`, `pip install .`
2. `runtime` (`python:3.14-slim`): Copy site-packages from builder, copy app source, set up non-root user

---

## RES-003: Python Dependency Installation in Docker

**Decision**: `pip install .` (non-editable install from `pyproject.toml`)

**Rationale**: Docker containers are immutable at runtime; editable installs (`-e`) serve no purpose. Installing without a virtual environment is the correct Docker pattern (the container IS the isolation boundary). The project constitution explicitly permits skipping venvs inside Docker image builds, provided this is documented.

**Constitution note**: The constitution's Python Discipline principle states "If a venv cannot be used (e.g., inside a Docker image build), the team MUST be consulted and the decision documented." **This research document serves as that documentation.** Virtual environments will continue to be used for all local development; Docker images install globally into the container.

**Layer caching strategy**: Copy `pyproject.toml` first, run `pip install .`, then copy source code — so dependency installs are cached until `pyproject.toml` changes.

---

## RES-004: Alembic Migration Entrypoint

**Decision**: Shell script `docker-entrypoint.sh` runs `alembic upgrade head` then `python -m app.main`.

**Rationale**: The existing `alembic/env.py` already reads `DATABASE_URL` from `settings.database_url` (pydantic-settings env var injection). In Docker, `DATABASE_URL` will point to the postgres service by container hostname. The entrypoint script uses `pg_isready` to wait for the database before running migrations, then exits non-zero if migrations fail (preventing the app from starting against an incompatible schema).

**Alembic working directory**: Must be run from `src/backend/` where `alembic.ini` resides. The Dockerfile `WORKDIR` is `/app/` (mapped to `src/backend/`).

---

## RES-005: Backend Health Check

**Decision**: Add a `GET /health` endpoint to the FastAPI app; Docker health check uses `curl -f http://localhost:8000/health`.

**Rationale**: The backend currently has no dedicated health endpoint. Using `/api/docs` or `/api/openapi.json` works but is slower and couples the health check to Swagger generation. A lightweight `/health → {"status": "ok"}` endpoint is the industry standard for container readiness probes.

**Implementation**: One new route outside the `/api/` prefix so the reverse proxy does not proxy it externally (or it can be at `/api/health` if preferred — decision left to implementation).

---

## RES-006: Non-Root Container User

**Decision**: Create a dedicated `appuser` (UID 10001) in all service images. Run all containers as this user.

**Rationale**: Running as non-root prevents privilege escalation if a container is compromised. UID >10000 avoids overlap with common system UIDs. File ownership is set via `COPY --chown` rather than post-copy `chown` (more cache-efficient).

---

## RES-007: Frontend Build Strategy

**Decision**: Two-stage Dockerfile — `builder` stage (`node:24-slim`) runs `npm ci && npm run build`; `production` stage (`nginx:1.29.5-alpine`) copies `dist/` and serves it.

**Rationale**:
- `node:24-slim` (Debian/glibc) is preferred over `node:24-alpine` for native module compatibility and is the Node.js official recommendation.
- `nginx:1.29.5-alpine` (~50MB) is the industry standard for serving Vue SPA static files. Version 1.27 is used for both the frontend and reverse proxy containers to keep the nginx version consistent across the stack.

**Dev mode**: A separate dev target in the Dockerfile (or `Dockerfile.dev`) runs `npm run dev` with Vite dev server; source code is volume-mounted so HMR works without rebuilding the image.

---

## RES-008: Frontend SPA Nginx Configuration

**Decision**: `try_files $uri $uri/ /index.html;` directive handles Vue Router history mode.

**Rationale**: When a user refreshes or navigates directly to a Vue route (e.g., `/auctions/123`), nginx must serve `index.html` instead of returning a 404. Vue Router then parses the URL client-side.

---

## RES-009: Vite Dev Server in Docker

**Decision**: Vite runs with `--host 0.0.0.0` (or `server.host: true` in vite.config) so it is reachable from outside the container. In Docker dev mode, the reverse proxy proxies to the Vite dev server.

**HMR/WebSocket**: The reverse proxy nginx must proxy WebSocket upgrade requests to the Vite dev server using `proxy_http_version 1.1` and `proxy_set_header Upgrade/Connection` headers. Vite's HMR config must point to `localhost:80` (the host port where nginx is exposed).

**Note**: The existing `vite.config.ts` has an `/api` proxy pointing to `http://localhost:8000`. In Docker dev mode, this Vite proxy is bypassed — the reverse proxy nginx handles routing instead. The Vite proxy config can remain as-is for non-Docker development.

---

## RES-010: Dedicated Reverse Proxy Service

**Decision**: Separate `nginx:1.29.5-alpine` container; the only container that exposes a host port (80).

**Routing**:
- `GET /api/*` → `http://backend:8000`
- `GET /*` → `http://frontend:80` (prod) or `http://frontend:5173` (dev)

**CORS impact**: Since the browser communicates exclusively with the reverse proxy on a single origin (`http://localhost`), all API calls are same-origin. FastAPI's CORS middleware can be restricted to `http://localhost` rather than permissive wildcards.

**WebSocket in dev**: An additional nginx location block proxies `/_vite` or WebSocket upgrade requests to the Vite dev server for HMR.

**Alternatives considered**:
- Combining frontend nginx and reverse proxy into one container — rejected: couples concerns and doesn't match production topology
- Traefik — rejected: adds operational complexity not justified for a two-service app

---

## RES-011: PostgreSQL Health Check

**Decision**: `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` in Compose health check; `depends_on: condition: service_healthy` for backend.

**Rationale**: `pg_isready` is a lightweight, purpose-built tool (included in the postgres image) that returns exit code 0 only when PostgreSQL accepts connections. More reliable than TCP port checks which succeed before Postgres is ready.

**Compose syntax (v2)**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

---

## RES-012: Restart Policy

**Decision**: `restart: on-failure` on all services.

**Rationale**: Containers restart automatically on non-zero exit (crash recovery) but not on clean stop (`docker compose stop`). This prevents infinite restart loops when a code error causes an immediate crash during development.

---

## RES-013: Image Registry

**Decision**: GitHub Container Registry (`ghcr.io`) as the default registry, documented in a `Makefile`.

**Rationale**: The project is hosted on GitHub. GHCR integrates natively with GitHub Actions with no extra authentication setup, has no rate limits for authenticated pulls, and images can be linked directly to the repository.

**Tagging strategy**: `ghcr.io/<owner>/<service>:<version>` where `<version>` defaults to the short git SHA (`git rev-parse --short HEAD`) and can be overridden with a semantic version tag.

**Makefile pattern**:
```makefile
REGISTRY ?= ghcr.io
ORG ?= $(shell git config --get remote.origin.url | sed 's/.*:\(.*\)\/.*/\1/')
VERSION ?= $(shell git rev-parse --short HEAD)
```

---

## RES-014: Docker Compose File Strategy

**Decision**: Two compose files — `docker-compose.yml` (production-like) + `docker-compose.dev.yml` (dev override).

**Rationale**:
- `docker-compose.yml` defines the full production-like stack (built images, optimized frontend, no source mounts)
- `docker-compose.dev.yml` overrides: mounts source code volumes, uses dev build targets, enables Vite HMR
- Dev usage: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
- Prod usage: `docker compose up`
- A `Makefile` provides short aliases: `make dev` and `make up`

---

## RES-015: .dockerignore Contents

**Backend** (`src/backend/.dockerignore`):
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.venv/`, `venv/`
- `.env`, `.env.*`
- `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`
- `pgo_auctions.db` (SQLite dev file)
- `*.egg-info/`

**Frontend** (`src/frontend/.dockerignore`):
- `node_modules/`
- `dist/`
- `.env`, `.env.*`
- `.vite/`
- `coverage/`
