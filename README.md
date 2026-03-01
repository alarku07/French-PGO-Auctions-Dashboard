# French PGO Auctions Dashboard

[French PGO Auctions Dashboard](https://french-pgo-auctions.onrender.com/)

A full-stack web application for tracking and visualising French Power Generation Option (PGO) auction data published on the [EEX exchange](https://www.eex.com). It automatically scrapes auction results and calendar events, stores them in a relational database, and presents interactive charts, statistics, and a filterable data table to end users.

---

## Table of Contents

- [About the Application](#about-the-application)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Disaster Recovery Plan](#disaster-recovery-plan)
- [Out of scope topics](#out-of-scope-topics)
- [Future ideas](#future-ideas)

---

## About the Application

French Power Guarantees of Origin (PGO) are capacity-market instruments auctioned periodically on the EEX platform. The results - volumes, bid counts, weighted-average prices - and the accompanying calendar of order-book open/close windows are published as HTML pages, PDF and Excel files.

This dashboard:
- **Syncs automatically** (daily, configurable) by scraping EEX pages and parsing Excel exports
- **Stores** auction results and auction events in a PostgreSQL database
- **Exposes** a versioned REST API for queries, statistics, and chart data
- **Displays** an interactive single-page dashboard with price/volume trend charts, a paginated auction table, upcoming-auction preview, and an auction-event calendar
- **Filters** results by region, technology type, and date range

### Development
This application has been developed (mostly) with [Claude Sonnet 4.6](https://www.anthropic.com/claude/sonnet) using [ Spec Kit](https://github.com/github/spec-kit) as AI-development framework

### Deployment
The application is deployed with the free plan on [Render](https://render.com/) cloud application platform.
- PostgreSQL DB provided as a service
- Backend running as Docker image
- Frontend served as a static website


- Application is accessible [French PGO Auctions Dashboard](https://french-pgo-auctions.onrender.com/)
- Backend swagger docs: [French PGO Auctions API Docs](https://french-pgo-auctions-dashboard.onrender.com/api/docs)

---

## Tech Stack

### Backend

| Technology | Version   | Why it was chosen |
|---|-----------|---|
| **Python** | 3.14+     | Mature ecosystem for data scraping, parsing (BeautifulSoup, openpyxl), and async I/O. |
| **FastAPI** | ≥ 0.115   | Native async support matches the async SQLAlchemy engine. Auto-generated OpenAPI docs reduce onboarding friction. Pydantic integration gives free request/response validation. |
| **SQLAlchemy 2.0** (async) | ≥ 2.0     | Async ORM means the DB driver never blocks the event loop during heavy sync jobs. The 2.0 `Mapped` / `mapped_column` API is explicit and fully type-checked. |
| **asyncpg** | ≥ 0.30    | The fastest pure-Python PostgreSQL driver; pairs naturally with the SQLAlchemy async engine. |
| **PostgreSQL 16** | 16-alpine | Reliable open-source RDBMS. Window functions and partial indexes make time-series price queries efficient. |
| **Alembic** | ≥ 1.14    | Schema migrations are version-controlled alongside code, enabling reproducible deployments and safe rollbacks. |
| **APScheduler** | ≥ 3.11    | Lightweight in-process scheduler; no extra infrastructure needed for the daily sync cron job. |
| **Uvicorn** | ≥ 0.34    | High-throughput ASGI server; production-grade with minimal configuration overhead. |
| **Pydantic Settings** | ≥ 2.7     | Reads config from environment variables with type coercion and validation — ideal for Docker-based deployments. |
| **structlog** | ≥ 25.1    | Structured (JSON) log output is easier to ingest into log aggregation platforms than plain-text logs. |
| **ruff + mypy** | latest    | Ruff replaces flake8/isort/pyupgrade with a single fast tool. Strict mypy ensures type errors are caught before runtime. |

### Frontend

| Technology | Version | Why it was chosen |
|---|---|---|
| **Node.js** | 24 | Runtime for the frontend build toolchain (Vite, TypeScript compilation, ESLint). Node 24 LTS provides stable V8 performance and native fetch, keeping the build environment current without chasing bleeding-edge releases. |
| **Vue 3** (Composition API) | 3.5 | The Composition API lets complex stateful logic (filters, pagination, chart data) live in focused composables rather than sprawling options objects. |
| **TypeScript** | 5.7 | End-to-end type safety; the same interface shapes used in API responses are reused across components, reducing mismatch bugs. |
| **Vite** | 6.1 | Sub-second hot-module replacement in development. Rollup-based production builds are small and tree-shaken. |
| **Axios** | 1.8 | Straightforward Promise-based HTTP client with interceptors; the single `api.ts` service file keeps all backend communication in one place. |
| **Apache ECharts + vue-echarts** | 5.6 | ECharts handles large time-series datasets (thousands of auction data points) without DOM performance degradation, and produces publication-quality SVG/Canvas charts. |
| **Vitest** | 3.0 | Vite-native test runner; shares the same config and module resolution as the app, eliminating the webpack-vs-jest config gap. |
| **ESLint 9** (flat config) | 9.x | Lint at CI time catches style regressions before they reach review. |

### Infrastructure

| Technology | Why it was chosen |
|---|---|
| **Docker + multi-stage builds** | Reproducible environments from laptop to CI to production. Multi-stage builds keep final images lean (Python slim + Nginx Alpine). |
| **Docker Compose** | Orchestrates four services (postgres, backend, frontend, nginx-proxy) with a single command, both in dev (hot-reload) and production modes. |
| **Nginx** | Serves the pre-built Vue static assets and reverse-proxies `/api/` to the FastAPI backend, offloading TLS termination and gzip compression from Python. |

---

## Architecture
Structure for independent fully dockerized solution.
```
                           ┌─────────────────────────────────────────────────────┐
                           │                   USER BROWSER                      │
                           └────────────────────────┬────────────────────────────┘
                                                    │ HTTP :80
                           ┌────────────────────────▼────────────────────────────┐
                           │                  NGINX PROXY                        │
                           │         (docker/nginx/nginx.conf)                   │
                           │  /          → frontend:80  (static Vue SPA)         │
                           │  /api/      → backend:8000 (FastAPI REST)           │
                           └──────────┬──────────────────────────┬───────────────┘
                                      │                          │
               ┌──────────────────────▼───────────┐  ┌───────────▼─────────────────────┐
               │         FRONTEND SERVICE         │  │       BACKEND SERVICE           │
               │   Nginx 1.29 / Alpine            │  │   Python 3.14 / Uvicorn         │
               │   Serves pre-built Vue 3 SPA     │  │   FastAPI + SQLAlchemy 2.0      │
               │                                  │  │                                 │
               │   Components:                    │  │   API Routes (/api/v1):         │
               │   ├─ AuctionTable.vue            │  │   ├─ /auctions                  │
               │   ├─ PriceChart.vue (ECharts)    │  │   ├─ /auctions/upcoming         │
               │   ├─ VolumeChart.vue (ECharts)   │  │   ├─ /auction-events            │
               │   ├─ StatsPanel.vue              │  │   ├─ /stats                     │
               │   ├─ AuctionEventList.vue        │  │   ├─ /charts/prices             │
               │   ├─ DateRangeFilter.vue         │  │   ├─ /charts/volumes            │
               │   └─ RegionFilter.vue            │  │   └─ /regions, /technologies    │
               │                                  │  │                                 │
               │   Composables:                   │  │   Services:                     │
               │   ├─ useAuctions.ts              │  │   ├─ SyncService (scraper)      │
               │   └─ useChartData.ts             │  │   └─ Parser (HTML/Excel)        │
               └──────────────────────────────────┘  │                                 │
                                                     │   Scheduler (APScheduler):      │
                           ┌─────────────────────────│─── daily sync @ 06:00 UTC ──┐   │
                           │                         │                             │   │
                           │   EEX WEBSITE           │                             │   │
                           │   eex.com               │◄────────────────────────────┘   │
                           │   (HTML pages           │   HTTPx scrape + parse          │
                           │    + Excel files)       │                                 │
                           └─────────────────────────┘ └──────────────────┬────────────┘
                                                                          │ asyncpg
                           ┌──────────────────────────────────────────────▼────────────┐
                           │                  POSTGRESQL 16                            │
                           │              (postgres:5432 / Docker volume)              │
                           │                                                           │
                           │  Tables:                                                  │
                           │  ├─ auctions        (results, volumes, prices)            │
                           │  ├─ auction_events  (calendar: open/close/matching)       │
                           │  └─ sync_logs       (sync history & error tracking)       │
                           │                                                           │
                           │  Migrations managed by Alembic                            │
                           └───────────────────────────────────────────────────────────┘


  ┌─────────────────── DATA FLOW ──────────────────────────────────────────────────────┐
  │                                                                                    │
  │  1. APScheduler triggers SyncService daily (or on-demand via API)                  │
  │  2. SyncService fetches EEX HTML/Excel → Parser extracts structured records        │
  │  3. Records are upserted (INSERT … ON CONFLICT DO UPDATE) — no duplicates          │
  │  4. SyncLog records outcome (success / error / rows affected)                      │
  │  5. Browser requests /api/v1/* → FastAPI queries PostgreSQL via AsyncSession       │
  │  6. Pydantic schemas serialise DB rows → JSON responses                            │
  │  7. Vue composables store responses in reactive state                              │
  │  8. ECharts renders time-series; table paginates locally                           │
  │                                                                                    │
  └────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Getting Started
The whole application is ready to be ran with a single docker compose command. Though it needs .env.docker file containing secrets for DB connection setup.

### Prerequisites

- Docker ≥ 24 and Docker Compose v2
- `make` (optional but recommended)

### Quick start (production mode)

```bash
cp .env.docker.example .env.docker
# Edit .env.docker — set POSTGRES_PASSWORD and DATABASE_URL at minimum
make up
# Dashboard: http://localhost
```

### Development mode (hot-reload)

```bash
make dev
# Vue HMR: http://localhost (proxied through Nginx dev config)
# Backend auto-reloads on file change
# PostgreSQL exposed on localhost:5432
```

### Data sync
On a fresh install the DB population has to be manually run as it is done once per environment.
```bash
# Initial DB population with existing data
python -m app.services.sync --backfill 

# Check and sync new data
python -m app.services.sync --manual
```

### CI checks (lint + type-check + tests + build)

```bash
make ci
```

### Running tests individually

```bash
# Backend
cd src/backend
python -m pytest tests/ -v

# Frontend
cd src/frontend
npx vitest run
```

---

## Disaster Recovery Plan

### Scope

This plan covers data loss, service outage, and corrupted state scenarios for the French PGO Auctions Dashboard.

---

### 1. Risk Register

| Risk | Likelihood | Impact | Mitigation                                                                                                                                |
|---|---|---|-------------------------------------------------------------------------------------------------------------------------------------------|
| PostgreSQL volume corruption | Low | High | Regular pg_dump backups + volume snapshots                                                                                                |
| Failed Alembic migration | Medium | High | Test migrations on staging; keep rollback scripts                                                                                         |
| EEX website structure change | Medium | Medium | Parser unit tests catch breakage; SyncLog tracks errors                                                                                   |
| Backend container crash | Low | Medium | Docker restart policy (`unless-stopped`); health-check endpoint                                                                           |
| Accidental data deletion | Low | High | `NEVER delete live data` rule (see CLAUDE.md); soft-delete pattern                                                                        |
| Secrets exposure | Low | Critical | `.env.docker` excluded from git; rotate credentials immediately if leaked. The only real secret is DB URL which contains DB user password |

---

### 2. Backup Strategy

#### Database backups

Run a daily `pg_dump` from within the compose network and ship to external storage:

```bash
# Example: dump to a timestamped file
docker compose exec postgres \
  pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip > backups/pgo_auctions_$(date +%Y%m%d_%H%M%S).sql.gz
```

Retention policy:
- **Daily** snapshots — retain 7 days
- **Weekly** snapshots — retain 4 weeks
- **Monthly** snapshots — retain 12 months

Store backups off-host (e.g., cloud object storage bucket with versioning enabled).

#### Docker volume snapshots

```bash
docker run --rm \
  -v french-pgo-auctions-dashboard_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz /data
```

---

### 3. Recovery Procedures

#### 3.1 Full database restore

```bash
# 1. Stop services
docker compose down

# 2. Drop and recreate the volume
docker volume rm french-pgo-auctions-dashboard_postgres_data
docker volume create french-pgo-auctions-dashboard_postgres_data

# 3. Start only postgres
docker compose up -d postgres

# 4. Restore from backup
gunzip -c backups/pgo_auctions_YYYYMMDD_HHMMSS.sql.gz \
  | docker compose exec -T postgres \
    psql -U $POSTGRES_USER $POSTGRES_DB

# 5. Restart all services
docker compose up -d
```

#### 3.2 Failed migration rollback

Alembic supports downgrades. Always record the current revision before upgrading:

```bash
# Check current revision
docker compose exec backend alembic current

# Downgrade one step
docker compose exec backend alembic downgrade -1

# Downgrade to a specific revision
docker compose exec backend alembic downgrade <revision_id>
```

Keep rollback scripts for every migration that drops columns or tables.

#### 3.3 Reseeding data from EEX (source-of-truth recovery)

Because all auction data originates from EEX, the database can be rebuilt from scratch by triggering a full sync:

```bash
# Truncate and resync (do NOT run on production without a prior backup)
docker compose exec backend python -c "
from app.services.sync import SyncService
import asyncio
asyncio.run(SyncService().run_full_historical_sync())
"
```

The upsert strategy (INSERT … ON CONFLICT DO UPDATE) means re-running the sync is idempotent - it will not duplicate records.

#### 3.4 Container / service restart

```bash
# Restart a single service
docker compose restart backend

# Full stack restart (non-destructive)
docker compose up -d --force-recreate
```

#### 3.5 Secrets rotation

1. Generate new database password
2. Update `.env.docker` with new `POSTGRES_PASSWORD` and `DATABASE_URL`
3. `docker compose down && docker compose up -d`
4. Revoke the old credential at the database level:
   ```sql
   ALTER ROLE pgo PASSWORD 'new_password';
   ```

---

### 4. Recovery Time Objectives

| Scenario | Target RTO | Target RPO |
|---|---|---|
| Container crash (auto-restart) | < 1 minute | 0 (no data loss) |
| Single service failure | < 5 minutes | 0 |
| Database restore from backup | < 30 minutes | ≤ 24 hours |
| Full environment rebuild | < 1 hour | ≤ 24 hours |
| Full data reseed from EEX | < 4 hours | 0 (EEX is source of truth) |

---

### 5. Monitoring & Alerting

- **Health endpoint:** `GET /health` — checked by Docker Compose every 30 s; returns 200 with DB connectivity status
- **SyncLog table:** every sync writes a record with status, row counts, and any error message — query it to detect silent parse failures
- **Structured logs:** `structlog` outputs JSON to stdout; ship to a log aggregation tool (e.g., Loki, Datadog) and alert on `ERROR` / `CRITICAL` entries
- **Recommended alert conditions:**
  - `/health` returning non-200 for > 2 consecutive checks
  - No successful sync entry in `sync_logs` for > 26 hours
  - PostgreSQL container not in `healthy` state

---

### 6. Runbook Quick Reference

```
Service down?          → docker compose ps  →  docker compose up -d <service>
DB connection error?   → check DATABASE_URL in .env.docker; check postgres health
Sync not running?      → check SYNC_ENABLED=true and APScheduler logs
Bad migration?         → alembic downgrade -1; fix migration; alembic upgrade head
Data looks wrong?      → query sync_logs for last run; check EEX for source changes
Secrets leaked?        → rotate immediately (section 3.5); audit git history
Full disaster?         → restore volume backup (section 3.1) or reseed (section 3.3)
```


## Out of scope topics
### Monitoring
Current solution doesn't provide any external monitoring.
- **Logs** - Back-end logs can only be read from std output on platform running the containers. Logs should be pushed somewhere where they are easy to analyze e.g. ElasticSearch or at least be configured to write files to external persistent location
- **Service health** - The application relies on docker health checks to try to recover on failures and errors. An external tool like Zabbix should perform health checks and monitor that services are running.

### Notifications
Current solution doesn't have access to notifications services like e-mail or sms.
- **Breaking external changes** - Application is unable to notify admin team if EEX site structure changes or any other change that requires updating the code

## Future ideas
- **Statistics** - Expand general statistics at the top of the page. Currently, there are 3 statistics, but there is room for more and relevant statistics.
- **Push notifications** - A user could subscribe for (e-mail) alerts when new auctions are published.
- **Export** - Allow user to download data e.g. as CSV or Excel.
- **Internationalization** - Multi-language support beyond English (e.g. Estonian, French etc.).
- **More data** - For example allow to view and search Account Holders from https://www.eex.com/en/markets/energy-certificates/french-power-gos/account-holder
