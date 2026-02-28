# Data Model: Docker Containerization Setup

**Branch**: `001-docker-setup` | **Date**: 2026-02-28

---

## Scope Note

This feature introduces no new data entities. The existing database schema (managed by Alembic migrations) is unchanged. The Docker setup wraps and deploys the existing data model without modification.

**Existing entities** (already defined in `src/backend/app/models/`):
- `Auction` — auction records scraped from EEX
- `AuctionEvent` — scheduled auction events
- `SyncLog` — history of sync operations

---

## Runtime Configuration Entities

The Docker feature introduces a structured set of **configuration variables** that constitute the runtime contract between the host environment and each container.

### Backend Service Configuration

| Variable | Description | Example (Docker) | Required |
|----------|-------------|-----------------|----------|
| `DATABASE_URL` | Async PostgreSQL connection string using container hostname | `postgresql+asyncpg://pgo:secret@postgres:5432/pgo_auctions` | Yes |
| `EEX_BASE_URL` | EEX website base URL | `https://www.eex.com` | Yes |
| `SYNC_ENABLED` | Enable/disable daily sync scheduler | `true` | Yes |
| `SYNC_SCHEDULE_HOUR` | Hour of daily sync (UTC) | `6` | Yes |
| `SYNC_SCHEDULE_MINUTE` | Minute of daily sync (UTC) | `0` | Yes |
| `LOG_LEVEL` | Structlog log level | `INFO` | Yes |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost` | Yes |
| `HOST` | Uvicorn bind host | `0.0.0.0` | Yes |
| `PORT` | Uvicorn listen port (internal) | `8000` | Yes |

### Database Service Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `POSTGRES_USER` | Database superuser name | `pgo` | Yes |
| `POSTGRES_PASSWORD` | Database superuser password | *(secret)* | Yes |
| `POSTGRES_DB` | Database name | `pgo_auctions` | Yes |

### Image Build Arguments

| Argument | Description | Example | Default |
|----------|-------------|---------|---------|
| `VERSION` | Semantic version or git SHA baked into image | `v1.2.3` or `a3f9c1d` | `dev` |
| `BUILD_DATE` | ISO 8601 build timestamp | `2026-02-28T10:00:00Z` | *(none)* |

---

## Service Topology

```
Host Machine (port 80)
        │
        ▼
  ┌─────────────┐
  │  nginx-proxy │  (nginx:1.29.5-alpine)
  │   port 80    │  ← sole host-exposed port
  └──────┬───────┘
         │
    ┌────┴──────────────────────┐
    │                           │
    ▼ /api/*                    ▼ /*
┌──────────┐              ┌──────────┐
│  backend  │              │ frontend │
│  :8000   │              │  :80     │
│ (FastAPI) │              │ (nginx)  │
└────┬─────┘              └──────────┘
     │
     ▼
┌──────────┐
│ postgres  │
│  :5432   │
└──────────┘

Internal Docker network (not host-exposed):
  backend, frontend, postgres, nginx-proxy
```

## Volume Entities

| Volume Name | Mounted In | Purpose | Persistence |
|-------------|-----------|---------|-------------|
| `postgres_data` | postgres:/var/lib/postgresql/data | Database files | Persists across container restarts |
| `./src/backend:/app` *(dev only)* | backend:/app | Source hot-reload | Bind mount to host |
| `./src/frontend/src:/app/src` *(dev only)* | frontend:/app/src | Source hot-reload | Bind mount to host |
