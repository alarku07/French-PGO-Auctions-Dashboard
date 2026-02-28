# Tasks: Docker Containerization Setup

**Input**: Design documents from `specs/001-docker-setup/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on other in-progress tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directory structure and shared configuration files that all later tasks depend on.

- [X] T001 Create `docker/nginx/` directory at project root (this directory holds both proxy configs)
- [X] T002 [P] Create `.env.docker.example` at project root with all required environment variables and safe placeholder defaults: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` (using postgres container hostname, e.g. `postgresql+asyncpg://pgo:secret@postgres:5432/pgo_auctions`), `EEX_BASE_URL`, `SYNC_ENABLED`, `SYNC_SCHEDULE_HOUR`, `SYNC_SCHEDULE_MINUTE`, `LOG_LEVEL`, `CORS_ORIGINS` (set to `http://localhost`), `HOST`, `PORT`
- [X] T003 [P] Append `.env.docker` to the root `.gitignore` file (create `.gitignore` at project root if it does not exist) — this prevents the secrets file from ever being committed to version control

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core files that MUST exist before any Dockerfile or Compose file can be written or tested.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Create `src/backend/.dockerignore` — exclude: `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `venv/`, `.env`, `.env.*`, `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`, `pgo_auctions.db`, `*.egg-info/`, `.git/`, `pgo_auctions_backend.egg-info/`
- [X] T005 [P] Create `src/frontend/.dockerignore` — exclude: `node_modules/`, `dist/`, `.env`, `.env.*`, `.vite/`, `coverage/`, `.git/`
- [X] T006 Add `GET /health` route to `src/backend/app/main.py` returning `{"status": "ok"}` with a 200 status — add it directly to the `app` instance (not under the `/api` router prefix) so Docker's internal health check can reach it via `curl http://localhost:8000/health` inside the container; this endpoint is not exposed through the reverse proxy and does not conflict with nginx-proxy's own `/health` response
- [X] T007 Create `src/backend/docker-entrypoint.sh` — script must: (1) `set -e` to exit on any error, (2) wait for PostgreSQL using `pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}"` in a loop with 2s sleep, (3) run `alembic upgrade head` from the `/app` working directory, (4) exec `python -m app.main`; make the script executable (`chmod +x`)

**Checkpoint**: Foundation ready — all user story phases can now begin.

---

## Phase 3: User Story 1 — Run Full Stack with One Command (Priority: P1) 🎯 MVP

**Goal**: A developer with only Docker installed runs `docker compose up --build` from the project root and the full application (reverse proxy + frontend + backend + database) is reachable at `http://localhost` within 90 seconds.

**Independent Test**: `docker compose up --build` → all four services show as healthy in `docker compose ps` → `http://localhost` loads the Vue frontend → `http://localhost/api/docs` loads the Swagger UI → `docker compose down` stops cleanly.

- [X] T008 [P] [US1] Create `src/backend/Dockerfile` with two stages: **builder** (`FROM python:3.14-slim AS builder`) installs `build-essential` and `postgresql-client` via apt, copies `pyproject.toml`, runs `pip install --no-cache-dir .`; **runtime** (`FROM python:3.14-slim`) installs `postgresql-client` only (needed for `pg_isready` in entrypoint), creates non-root `appuser` with UID 10001 (`groupadd -r appuser && useradd -r -g appuser -u 10001 appuser`), copies `/usr/local/lib/python3.14/site-packages/` from builder, copies app source with `--chown=appuser:appuser`, copies `docker-entrypoint.sh`, sets `WORKDIR /app`, `USER appuser`, `ENV PYTHONUNBUFFERED=1`, `ARG VERSION=dev`, `ARG BUILD_DATE`, `ENTRYPOINT ["/app/docker-entrypoint.sh"]`
- [X] T009 [P] [US1] Create `src/frontend/Dockerfile` with two stages: **builder** (`FROM node:24-slim AS builder`) copies `package*.json`, runs `npm ci`, copies remaining source, runs `npm run build`; **runtime** (`FROM nginx:1.29.5-alpine`) copies `dist/` from builder to `/usr/share/nginx/html`, embeds an inline nginx server block in `/etc/nginx/conf.d/default.conf` with `listen 80`, `root /usr/share/nginx/html`, `try_files $uri $uri/ /index.html` for SPA routing, and gzip enabled for js/css/html; `ARG VERSION=dev`; `EXPOSE 80`
- [X] T010 [P] [US1] Create `docker/nginx/nginx.conf` — define two upstream blocks (`upstream backend { server backend:8000; }` and `upstream frontend { server frontend:80; }`); single server block on port 80; `location /health { access_log off; return 200 "ok\n"; add_header Content-Type text/plain; }`; `location /api/ { proxy_pass http://backend; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; proxy_connect_timeout 60s; proxy_read_timeout 60s; }`; `location / { proxy_pass http://frontend; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }`
- [X] T011 [US1] Create `docker-compose.yml` at project root with four services: **postgres** (`image: postgres:16-alpine`, env vars `POSTGRES_USER/PASSWORD/DB` from env file, `healthcheck: test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"] interval: 10s timeout: 5s retries: 5 start_period: 30s`, `restart: on-failure`, named volume `postgres_data:/var/lib/postgresql/data`); **backend** (`build: context: src/backend`, `env_file: .env.docker`, `depends_on: postgres: condition: service_healthy`, `healthcheck: test: ["CMD", "curl", "-f", "http://localhost:8000/health"] interval: 15s timeout: 5s retries: 3 start_period: 40s`, `restart: on-failure`); **frontend** (`build: context: src/frontend`, no `depends_on` — static file serving does not require the backend to be running, so frontend starts in parallel with backend to stay within SC-002's 90s target; `restart: on-failure`); **nginx-proxy** (`image: nginx:1.29.5-alpine`, `ports: ["80:80"]`, volume mount `./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro`, `depends_on: frontend: condition: service_started, backend: condition: service_healthy`, `restart: on-failure`); define named volume `postgres_data`

**Checkpoint**: `docker compose up --build` starts all services → `docker compose ps` shows all healthy → `http://localhost` serves the Vue app → `http://localhost/api/docs` serves Swagger UI.

---

## Phase 4: User Story 2 — Build, Tag, and Push Individual Service Images (Priority: P2)

**Goal**: A developer or CI system can build either service image independently, tag it with a version or git SHA, and push it to GitHub Container Registry using documented Makefile commands.

**Independent Test**: `make build SERVICE=backend VERSION=smoke-test` succeeds and produces a tagged image; `docker run --rm --env-file .env.docker <image>` starts the backend (migrations run, then process exits after DB unavailable — confirming the image is functional); image push workflow documented in quickstart.md.

- [X] T012 [US2] Create `Makefile` at project root with the following variables and targets — **Variables**: `REGISTRY ?= ghcr.io`, `ORG ?= $(shell git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\)\/.*/\1/')`, `VERSION ?= $(shell git rev-parse --short HEAD)`, `BUILD_DATE := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)`, `BACKEND_IMAGE := $(REGISTRY)/$(ORG)/pgo-auctions-backend`, `FRONTEND_IMAGE := $(REGISTRY)/$(ORG)/pgo-auctions-frontend`; **Targets**: `up` (docker compose up --build), `dev` (docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build), `down` (docker compose down), `build` (if SERVICE=backend build backend only; if SERVICE=frontend build frontend only; default builds both — each uses `--build-arg VERSION=$(VERSION) --build-arg BUILD_DATE=$(BUILD_DATE)` and tags as `$(IMAGE):$(VERSION)` and `$(IMAGE):latest`), `push` (docker push VERSION tag + latest tag for specified or both services; add a comment in the Makefile documenting the prerequisite `docker login ghcr.io` step), `ci` (runs `cd src/backend && ruff check app/ && mypy app/ && python -m pytest tests/ -v`; then `cd src/frontend && npx eslint src/ && npx vue-tsc --noEmit && npx vitest run`; then `make build`)

**Checkpoint**: `make build SERVICE=backend VERSION=v0.1.0` produces image tagged `ghcr.io/<org>/pgo-auctions-backend:v0.1.0`; `make ci` runs all quality gates before building.

---

## Phase 5: User Story 3 — Environment-Specific Configuration (Priority: P3)

**Goal**: `make dev` starts the stack in development mode with Vite hot-reload; a source file change in `src/frontend/src/` or `src/backend/app/` is reflected without restarting containers; `make up` (no dev override) runs the optimised production build.

**Independent Test**: `make dev` → edit `src/frontend/src/App.vue` (add a visible text change) → browser reflects the change within 5 seconds without restarting containers (SC-003 frontend HMR) → edit `src/backend/app/api/stats.py` or any backend file → confirm via `curl http://localhost/api/docs` that the backend reloaded within 5 seconds (SC-003 backend hot-reload) → `make down` → `make up` → confirm production static assets are served with no Vite dev server running.

- [X] T013 [P] [US3] Update `src/frontend/vite.config.ts` — add `host: true` inside the existing `server` block (alongside `port: 5173` and the existing `proxy` config) so the Vite dev server binds to `0.0.0.0` and is reachable from the nginx container; also add `hmr: { host: 'localhost', port: 80, protocol: 'ws' }` so the browser HMR WebSocket connects through nginx on port 80
- [X] T014 [P] [US3] Add a `dev` build stage to `src/frontend/Dockerfile` — insert `FROM node:24-slim AS dev` after the builder stage; copy `node_modules/` from builder (`COPY --from=builder /app/node_modules ./node_modules`); copy all remaining source (`COPY . .`); `EXPOSE 5173`; `CMD ["npm", "run", "dev"]`
- [X] T015 [P] [US3] Create `docker/nginx/nginx.dev.conf` — same as `nginx.conf` but change `upstream frontend { server frontend:5173; }` and update `location /` to add WebSocket upgrade support: `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 86400s; proxy_buffering off;` (required for Vite HMR WebSocket to pass through nginx)
- [X] T016 [US3] Create `docker-compose.dev.yml` at project root — override three services: **backend** (add `volumes: ["./src/backend:/app"]` and override `command` to `["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]`); **frontend** (set `build: target: dev`, add `volumes: ["./src/frontend:/app", "frontend_node_modules:/app/node_modules"]` to prevent host node_modules overwriting the container's installed modules); **nginx-proxy** (change volume mount to `./docker/nginx/nginx.dev.conf:/etc/nginx/nginx.conf:ro`); also expose `postgres: ports: ["5432:5432"]` for optional local DB tool access; define named volume `frontend_node_modules`

**Checkpoint**: `make dev` → edit frontend source → browser hot-reloads < 5s → edit backend source → API reflects change < 5s → `make down` → `make up` → production static files served, no HMR.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the implementation against the quickstart guide and confirm all success criteria.

- [X] T017 [P] Review `specs/001-docker-setup/quickstart.md` and update any commands or file paths that changed during implementation (e.g. exact `make` targets, env var names, URLs); confirm `docker login ghcr.io` prerequisite is documented before the push workflow
- [ ] T018 Run the full smoke test: `make dev` → verify frontend HMR → verify backend hot-reload → `make down` → `make up` → verify production build at `http://localhost` and API at `http://localhost/api/docs` → `make down` → confirm `postgres_data` volume survived restart by checking data persists after `make down && make up`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002 and T003 are parallel
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories; T004 and T005 are parallel
- **US1 (Phase 3)**: Depends on Phase 2 completion; T008, T009, T010 are parallel; T011 depends on all three
- **US2 (Phase 4)**: Depends on Phase 2; T012 can start in parallel with Phase 3
- **US3 (Phase 5)**: Depends on Phase 3 (needs `docker-compose.yml` as base); T013, T014, T015 are parallel; T016 depends on all three
- **Polish (Phase 6)**: Depends on all story phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — no dependencies on US2 or US3
- **US2 (P2)**: Depends on Foundational only — independent of US1/US3 (Makefile wraps existing compose files)
- **US3 (P3)**: Depends on US1 (needs `docker-compose.yml` to extend) — independent of US2

### Within Each Phase

- T008, T009, T010 (Phase 3): All parallel — different files
- T011 (Phase 3): Depends on T008, T009, T010
- T013, T014, T015 (Phase 5): All parallel — different files
- T016 (Phase 5): Depends on T013, T014, T015

---

## Parallel Opportunities

### Phase 1 (Setup)
```
Parallel: T002 (.env.docker.example) + T003 (.gitignore update)
Sequential after: Phase 2 begins
```

### Phase 2 (Foundational)
```
Parallel: T004 (backend .dockerignore) + T005 (frontend .dockerignore)
Sequential after: T006 (health endpoint), T007 (entrypoint.sh)
```

### Phase 3 (US1)
```
Parallel: T008 (backend Dockerfile) + T009 (frontend Dockerfile) + T010 (nginx.conf)
Sequential after: T011 (docker-compose.yml — needs all three)
```

### Phase 5 (US3)
```
Parallel: T013 (vite.config.ts) + T014 (frontend dev stage) + T015 (nginx.dev.conf)
Sequential after: T016 (docker-compose.dev.yml — needs all three)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T007) — **CRITICAL, blocks everything**
3. Complete Phase 3: US1 (T008–T011)
4. **STOP and VALIDATE**: `docker compose up --build` → app accessible at `http://localhost`
5. Demo-ready: full stack runs from a single command

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. US1 complete → `docker compose up --build` works → **ship as MVP**
3. US2 complete → `make build` + `make push` → images publishable to GHCR
4. US3 complete → `make dev` → hot-reload developer workflow ready
5. Polish → validated against quickstart, smoke tested

### Parallel Team Strategy

With two developers after Phase 2 is complete:
- **Developer A**: Phase 3 (US1) — all container + compose files
- **Developer B**: Phase 4 (US2) — Makefile (can work against compose files once merged)
- Then together: Phase 5 (US3) — dev overrides

---

## Notes

- Tasks marked [P] operate on different files with no in-flight dependencies — safe to parallelise
- [Story] label maps each task to its user story for traceability to spec.md
- `docker-entrypoint.sh` must be created with execute permission — verify with `git ls-files --stage src/backend/docker-entrypoint.sh` (should show mode 100755)
- The `.env.docker` file (created from `.env.docker.example`) is blocked from commits by T003's `.gitignore` entry
- Backend `WORKDIR` in Dockerfile must be `/app` so `alembic.ini` (at `src/backend/alembic.ini`, copied to `/app/alembic.ini`) is found by the entrypoint
- site-packages copy path in multi-stage build: `/usr/local/lib/python3.14/site-packages/`
- frontend starts in parallel with backend in `docker-compose.yml` (no `depends_on` on backend) — intentional for SC-002 compliance
- Stop at any checkpoint to validate the story independently before proceeding
