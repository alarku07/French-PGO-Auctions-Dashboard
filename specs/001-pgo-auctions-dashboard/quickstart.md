# Quickstart: French PGO Auctions Dashboard

**Feature**: 001-pgo-auctions-dashboard
**Date**: 2026-02-23

## Prerequisites

- Python 3.13+
- Node.js 24+ / npm 11+
- PostgreSQL 16+ (for development) or SQLite (for POC only)
- Git

## Project Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd "French PGO Auctions Dashboard"
git checkout 001-pgo-auctions-dashboard
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install dependencies
cd src/backend
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your database URL:
#   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/pgo_auctions
#   For POC/mock-up only: DATABASE_URL=sqlite+aiosqlite:///./pgo_auctions.db

# Run database migrations
alembic upgrade head

# Start the backend server
python -m app.main
# Output: [PGO-API] running on port 8000 (PID: <pid>)
```

### 3. Frontend Setup

```bash
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Output: [PGO-UI] running on port 5173 (PID: <pid>)
```

### 4. Open the Dashboard

Navigate to `http://localhost:5173` in your browser.

On first launch (empty database), the dashboard displays a message guiding the operator to run the initial data sync.

## Data Sync

### Initial Backfill (one-time)

Populates the database with all historical auction data from EEX ZIP archives:

```bash
cd src/backend
python -m app.services.sync --backfill
```

This downloads ZIP archives for 2019-2023, 2024-2025, and 2026, extracts all Excel files, parses them, and inserts records into the database. Takes approximately 1-2 minutes.

**Idempotent**: Safe to re-run. Duplicate records are skipped via the composite key. Downloaded ZIPs are cached in `data/downloads/` to avoid redundant downloads.

### Manual Sync (latest results)

Fetches the latest auction results from the EEX webpage:

```bash
cd src/backend
python -m app.services.sync --manual
```

### Automatic Daily Sync

The backend includes an in-process scheduler (APScheduler) that runs a sync job daily at 06:00 UTC. This is enabled by default when the backend server is running. Configure via `.env`:

```
SYNC_ENABLED=true
SYNC_SCHEDULE_HOUR=6
SYNC_SCHEDULE_MINUTE=0
```

**Important**: When `SYNC_ENABLED=true`, run uvicorn with exactly **1 worker** to prevent duplicate sync executions. Multi-worker deployments should disable the in-process scheduler and use an external cron trigger instead.

## Quality Gates

Before committing any code, all three gates must pass:

### Backend

```bash
cd src/backend

# Lint
ruff check .

# Type check
mypy .

# Tests
pytest
```

### Frontend

```bash
cd src/frontend

# Lint
npx eslint .

# Type check
npx vue-tsc --noEmit

# Tests
npx vitest run
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL or SQLite async connection string |
| `EEX_BASE_URL` | No | `https://www.eex.com` | EEX website base URL |
| `SYNC_ENABLED` | No | `true` | Enable automatic daily sync |
| `SYNC_SCHEDULE_HOUR` | No | `6` | Hour (UTC) for daily sync |
| `SYNC_SCHEDULE_MINUTE` | No | `0` | Minute for daily sync |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `HOST` | No | `0.0.0.0` | Backend server bind address |
| `PORT` | No | `8000` | Backend server port |
