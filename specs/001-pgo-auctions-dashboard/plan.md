# Implementation Plan: French PGO Auctions Dashboard

**Branch**: `001-pgo-auctions-dashboard` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pgo-auctions-dashboard/spec.md`

## Summary

Build a publicly accessible, read-only dashboard that visualises French Power Guarantees of Origin auction results sourced from EEX. The system comprises an async Python backend (FastAPI) serving a REST API over a PostgreSQL database, a Vue.js SPA frontend with interactive charts (Apache ECharts), and an automated daily sync process that fetches auction results and calendar data from the EEX website. Historical backfill is handled via ZIP archives of monthly Excel files provided by EEX.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript + Vue.js 3 (frontend)
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy (async), httpx, beautifulsoup4, openpyxl, APScheduler, uvicorn
- Frontend: Vue.js 3 (Composition API), Apache ECharts (via vue-echarts), Axios, Vue Router
**Storage**: PostgreSQL (production/development), SQLite (POC/mock-ups only)
**Testing**: pytest + pytest-asyncio (backend), Vitest (frontend)
**Target Platform**: Linux server (production), Windows/macOS/Linux (development)
**Project Type**: Web application (SPA frontend + REST API backend)
**Performance Goals**: Dashboard initial load < 3s, chart filter response < 2s (SC-002), page load to first useful content < 10s (SC-001)
**Constraints**: Responsive 320px–1920px, no authentication, no PII collection, daily sync resilience
**Scale/Scope**: ~12 regions x ~84 months (7 years) x 4 technologies = ~4,000 auction records, single-page dashboard with 2 interactive charts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Data Integrity | PostgreSQL for dev/prod; SQLite only for POC. No destructive operations on live data. Sync uses upsert-or-skip deduplication. | PASS |
| II | Quality Gates | Linting (ruff + ESLint), type checking (mypy + TypeScript strict), unit tests (pytest + Vitest) — all green before every commit. | PASS |
| III | Python Discipline | Virtual environment (.venv) mandatory. PEP 8 + double quotes. Async-first (FastAPI, httpx, SQLAlchemy async). Python 3.13. | PASS |
| IV | Frontend Standards | Vue.js 3 Composition API. Responsive 320px–1920px. Business logic in composables/services, not templates. ESLint mandatory. Keyboard-navigable controls with ARIA attributes. | PASS |
| V | Observability | Service startup prints `[SERVICE NAME] running on port [PORT] (PID: [PID])`. Structured JSON logging on every API endpoint with timestamp, request ID, path, method, status, duration. | PASS |

**Pre-Phase 0 verdict**: All gates PASS. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-pgo-auctions-dashboard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-contract.md  # REST API endpoint specifications
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Settings and environment config
│   │   ├── database.py          # SQLAlchemy async engine/session
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── auction.py       # Auction model (past results + upcoming, single table)
│   │   │   └── sync_log.py      # SyncLog model
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   └── auction.py
│   │   ├── api/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Main API router
│   │   │   ├── auctions.py      # Auction endpoints
│   │   │   └── stats.py         # Statistics endpoints
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── sync.py          # EEX sync service
│   │   │   └── parser.py        # Excel/ZIP parser
│   │   └── middleware/          # Security headers, logging
│   │       ├── __init__.py
│   │       └── security.py
│   ├── pyproject.toml           # Python project config + dependencies
│   └── alembic/                 # Database migrations
│       ├── alembic.ini
│       └── versions/
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── components/          # Reusable UI components
│   │   │   ├── AuctionTable.vue
│   │   │   ├── UpcomingAuctions.vue
│   │   │   ├── StatsPanel.vue
│   │   │   ├── PriceChart.vue
│   │   │   ├── VolumeChart.vue
│   │   │   ├── RegionFilter.vue
│   │   │   ├── DateRangeFilter.vue
│   │   │   └── LastUpdated.vue
│   │   ├── composables/         # Shared logic (useAuctions, useChartData)
│   │   ├── services/            # API client (axios)
│   │   └── assets/              # Styles, fonts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── eslint.config.js
tests/
├── backend/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
└── frontend/
    └── unit/
docs/
```

**Structure Decision**: Web application layout per CLAUDE.md — `src/backend/` for Python FastAPI, `src/frontend/` for Vue.js SPA, `tests/` at repository root. This matches the constitution's Source Layout and the project's CLAUDE.md rules.

## Constitution Re-Check (Post-Phase 1 Design)

| # | Principle | Post-Design Verification | Status |
|---|-----------|--------------------------|--------|
| I | Data Integrity | Data model uses composite unique key for upsert-or-skip deduplication (FR-016). No destructive operations in sync logic. PostgreSQL for dev/prod confirmed in quickstart.md. | PASS |
| II | Quality Gates | quickstart.md documents all three gate commands (ruff, mypy, pytest for backend; eslint, vue-tsc, vitest for frontend). | PASS |
| III | Python Discipline | Backend uses FastAPI (async), httpx (async HTTP), SQLAlchemy async engine, structlog. All async-first. pyproject.toml will pin versions. PEP 8 + double quotes enforced via ruff config. | PASS |
| IV | Frontend Standards | Vue.js 3 Composition API. Responsive 320px–1920px per data-model and contract design. Business logic in composables/services. ESLint configured. ARIA attributes required per spec. | PASS |
| V | Observability | API contract includes structured JSON logging fields. Quickstart shows service startup format: `[SERVICE NAME] running on port [PORT] (PID: <pid>)`. | PASS |

**Post-Phase 1 verdict**: All gates PASS. Design is constitution-compliant.

## Complexity Tracking

> No constitution violations. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
