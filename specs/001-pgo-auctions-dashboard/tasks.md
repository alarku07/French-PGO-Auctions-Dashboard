# Tasks: French PGO Auctions Dashboard

**Input**: Design documents from `/specs/001-pgo-auctions-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contract.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — directory structure, dependency manifests, tooling configuration.

- [X] T001 Create project directory structure per plan.md: `src/backend/app/`, `src/backend/app/models/`, `src/backend/app/schemas/`, `src/backend/app/api/`, `src/backend/app/services/`, `src/backend/app/middleware/`, `src/backend/alembic/versions/`, `src/frontend/src/`, `src/frontend/src/components/`, `src/frontend/src/composables/`, `src/frontend/src/services/`, `src/frontend/src/assets/`, `tests/backend/unit/`, `tests/backend/integration/`, `tests/frontend/unit/`, `docs/`, `data/downloads/`
- [X] T002 Create backend Python project manifest with all dependencies (FastAPI, SQLAlchemy[asyncio], asyncpg, aiosqlite, httpx, beautifulsoup4, openpyxl, APScheduler, uvicorn, structlog, alembic, pydantic-settings) and dev dependencies (ruff, mypy, pytest, pytest-asyncio) in `src/backend/pyproject.toml`
- [X] T003 [P] Initialize Vue.js 3 frontend project with Vite, TypeScript, vue-echarts, echarts, axios, and vue-router in `src/frontend/` (package.json, tsconfig.json, vite.config.ts, index.html)
- [X] T004 [P] Configure backend linting and type checking: ruff config (PEP 8, double quotes enforced) in `src/backend/pyproject.toml` [tool.ruff] section; mypy config in `src/backend/pyproject.toml` [tool.mypy] section
- [X] T005 [P] Configure frontend linting: ESLint with TypeScript and Vue plugins in `src/frontend/eslint.config.js`
- [X] T006 [P] Update `.gitignore` to include: `.venv/`, `node_modules/`, `__pycache__/`, `*.pyc`, `.env`, `data/downloads/`, `dist/`, `.mypy_cache/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure and frontend shell that ALL user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

### Backend Core

- [X] T007 Implement application configuration with pydantic-settings in `src/backend/app/config.py` — load DATABASE_URL, EEX_BASE_URL, SYNC_ENABLED, SYNC_SCHEDULE_HOUR, SYNC_SCHEDULE_MINUTE, LOG_LEVEL, CORS_ORIGINS, HOST, PORT from environment. Create `.env.example` at `src/backend/.env.example` with documented defaults per quickstart.md
- [X] T008 Implement async database engine and session factory using SQLAlchemy async in `src/backend/app/database.py` — create async engine from DATABASE_URL, async sessionmaker, Base declarative model, and a `get_session` async dependency for FastAPI
- [X] T009 [P] Implement Auction SQLAlchemy model in `src/backend/app/models/auction.py` — all fields per data-model.md (id, auction_date, region, production_period, technology, status, volume_offered_mwh, volume_allocated_mwh, num_bids, num_winning_bids, weighted_avg_price_eur, reserve_price_eur, order_book_open, order_book_close, order_matching, created_at, updated_at). Include composite unique constraint on (auction_date, region, production_period, technology). Include all CHECK constraints from data-model.md. Include indexes: idx_auction_date, idx_auction_region, idx_auction_status
- [X] T010 [P] Implement SyncLog SQLAlchemy model in `src/backend/app/models/sync_log.py` — all fields per data-model.md (id, run_timestamp, completed_at, outcome, sync_type, records_added, records_updated, records_skipped, error_message, created_at). Include indexes: idx_sync_timestamp (DESC), idx_sync_outcome
- [X] T011 Create models package `__init__.py` at `src/backend/app/models/__init__.py` — export Auction and SyncLog
- [X] T012 Configure Alembic for async SQLAlchemy: create `src/backend/alembic.ini` and `src/backend/alembic/env.py` with async migration support. Generate initial migration for Auction and SyncLog tables in `src/backend/alembic/versions/`
- [X] T013 [P] Create Pydantic response schemas in `src/backend/app/schemas/auction.py` — AuctionResponse, UpcomingAuctionResponse, AuctionListResponse (with pagination), StatsResponse, PriceChartDataPoint, VolumeChartDataPoint, ChartResponse, RegionListResponse, ErrorResponse per api-contract.md
- [X] T014 Create schemas package `__init__.py` at `src/backend/app/schemas/__init__.py`

### Backend Middleware & Infrastructure

- [X] T015 Implement security headers middleware in `src/backend/app/middleware/security.py` — add Content-Security-Policy, X-Frame-Options (DENY), X-Content-Type-Options (nosniff), Referrer-Policy, Permissions-Policy headers to every response per api-contract.md FR-019
- [X] T016 [P] Implement structured logging configuration in `src/backend/app/middleware/__init__.py` — configure structlog for JSON output with timestamp (ISO 8601), request_id (UUID), path, method, status, duration_ms per Constitution Principle V. Add request logging middleware that logs every API request
- [X] T017 Create the main API router in `src/backend/app/api/router.py` — mount sub-routers for auctions, stats, charts, regions under `/api/v1` prefix. Create `src/backend/app/api/__init__.py`
- [X] T018 Implement FastAPI application entry point in `src/backend/app/main.py` — create FastAPI app, add CORS middleware (configurable origins from config), mount security headers middleware, mount logging middleware, include API router, add lifespan handler for database setup. Print `[PGO-API] running on port {PORT} (PID: {pid})` on startup per Constitution Principle V. Create `src/backend/app/__init__.py`

### Frontend Shell

- [X] T019 Create global CSS with EEX visual identity in `src/frontend/src/assets/styles.css` — CSS custom properties for colours (dark navy text #1a1a2e, white background #ffffff, light grey sections #f5f5f5, green accent for links/highlights, dark header bar), sans-serif font stack, responsive breakpoints (320px, 768px, 1024px, 1920px), table styling (dark header, zebra striping), card component base styles
- [X] T020 [P] Create Axios API client service in `src/frontend/src/services/api.ts` — configure base URL (`/api/v1`), typed functions for each endpoint: `getAuctions(params)`, `getUpcomingAuctions()`, `getStats()`, `getChartPrices(params)`, `getChartVolumes(params)`, `getRegions()`, `getTechnologies()`. Include response types matching api-contract.md schemas
- [X] T021 Create App.vue shell with responsive layout in `src/frontend/src/App.vue` — header with dashboard title and EEX-inspired styling, main content area with CSS grid/flexbox for responsive layout, footer with "Last updated" placeholder. Import global styles. Create `src/frontend/src/main.ts` that mounts the app
- [X] T022 Create empty test configuration files: `tests/backend/conftest.py` (pytest fixtures for async DB session with SQLite for testing), `tests/backend/unit/__init__.py`, `tests/backend/integration/__init__.py`, `tests/frontend/unit/__init__.py`

### Foundational Tests

- [X] T053 [P] Add sync deduplication smoke test in `tests/backend/unit/test_sync_dedup.py` — seed an in-memory SQLite database with sample Auction records, attempt to insert duplicates using the composite key (auction_date, region, production_period, technology), and verify that duplicates are skipped and existing non-NULL fields are never overwritten. Covers FR-016 deduplication logic
- [X] T054 [P] Add stats aggregation smoke test in `tests/backend/unit/test_stats.py` — seed an in-memory SQLite database with known auction records, call the stats computation logic, and verify total_auctions_held count, total_volume_awarded_mwh sum, and overall_weighted_avg_price_eur weighted average match expected values. Covers FR-004 aggregate statistics
- [X] T055 [P] Add API validation smoke test in `tests/backend/unit/test_api_validation.py` — use FastAPI TestClient to verify: GET /api/v1/auctions returns 400 for invalid date format, GET /api/v1/auctions returns 400 for page_size > 200, GET /api/v1/auctions/upcoming returns 200 with empty list when no upcoming auctions exist. Covers input validation and empty-state handling

**Checkpoint**: Foundation ready — backend serves empty API at `http://localhost:8000/api/v1`, frontend shell renders at `http://localhost:5173`. Lint, type check, and tests pass green.

---

## Phase 3: User Story 1 — Auction Dashboard Overview (Priority: P1)

**Goal**: An energy professional opens the dashboard and sees past auction results, upcoming auctions, aggregate statistics, and the last-updated timestamp — all on one page.

**Independent Test**: Open `http://localhost:5173` with a pre-seeded database. Verify: at least one past auction result visible, at least one upcoming auction date visible, "Last updated" timestamp shown, aggregate statistics displayed. Testable independently of sync logic.

### Backend Endpoints for US1

- [X] T023 [US1] Implement GET /api/v1/auctions endpoint in `src/backend/app/api/auctions.py` — query Auction table where status='past', support query params: start_date, end_date (default: previous calendar month), region, technology, page, page_size (max 200), sort_by, sort_order per api-contract.md. Return paginated AuctionListResponse. Validate inputs; return 400 ErrorResponse for invalid params
- [X] T024 [US1] Implement GET /api/v1/auctions/upcoming endpoint in `src/backend/app/api/auctions.py` — query Auction table where status='upcoming', ordered by auction_date ASC. Return list with count. Return empty list with count=0 if none exist (FR-002 acceptance scenario 5)
- [X] T025 [P] [US1] Implement GET /api/v1/stats endpoint in `src/backend/app/api/stats.py` — compute total_auctions_held (COUNT DISTINCT auction_date where past), total_volume_awarded_mwh (SUM where past AND technology IS NULL), overall_weighted_avg_price_eur (weighted average where past AND technology IS NULL), last_updated (MAX completed_at from SyncLog where outcome='success'). Return StatsResponse per api-contract.md
- [X] T026 [P] [US1] Implement GET /api/v1/regions endpoint in `src/backend/app/api/auctions.py` — query DISTINCT region from Auction table, ordered alphabetically. Return RegionListResponse

### Frontend Components for US1

- [X] T027 [P] [US1] Create AuctionTable component in `src/frontend/src/components/AuctionTable.vue` — display past auctions in a responsive table with columns: Auction Date, Region, Volume Offered (MWh), Volume Awarded (MWh), Avg. Clearing Price (EUR/MWh). Default to previous calendar month. Include DateRangeFilter integration. Show "Not yet published" for null price/volume fields. Zebra-striped rows with dark header per EEX styling. Mobile-responsive: stack cards below 768px
- [X] T028 [P] [US1] Create DateRangeFilter component in `src/frontend/src/components/DateRangeFilter.vue` — two date inputs (start/end) with sensible defaults (previous calendar month). Emit filter-change event with {start_date, end_date}. Responsive layout
- [X] T029 [P] [US1] Create UpcomingAuctions component in `src/frontend/src/components/UpcomingAuctions.vue` — display upcoming auctions in a compact list/table showing auction date and region. If no upcoming auctions, show "No auctions currently scheduled" message (acceptance scenario 5). Include order book open/close dates if available
- [X] T030 [P] [US1] Create StatsPanel component in `src/frontend/src/components/StatsPanel.vue` — display three stat cards: Total Auctions Held, Total Volume Awarded (MWh), Overall Avg. Price (EUR/MWh). Format numbers with thousand separators. Responsive grid (3 columns desktop, stack on mobile)
- [X] T031 [P] [US1] Create LastUpdated component in `src/frontend/src/components/LastUpdated.vue` — display "Last updated: [formatted timestamp]" or "No data synced yet — run initial sync" if null. Format as relative time + absolute datetime on hover
- [X] T032 [US1] Create useAuctions composable in `src/frontend/src/composables/useAuctions.ts` — reactive state for auctions, upcoming, stats, regions, lastUpdated. Functions to fetch each endpoint via api.ts. Loading and error states. Called from App.vue to populate all US1 components
- [X] T033 [US1] Assemble dashboard layout in `src/frontend/src/App.vue` — integrate StatsPanel, LastUpdated, AuctionTable (with DateRangeFilter), and UpcomingAuctions components. Arrange in responsive grid: stats panel across top, auction table and upcoming auctions side-by-side on desktop, stacked on mobile. Handle empty database state: show guidance message to run initial sync

**Checkpoint**: Dashboard overview fully functional. Past auctions displayed with date-range filtering, upcoming auctions listed, stats computed, last-updated shown. All testable with a manually seeded database. Lint, type check, tests pass.

---

## Phase 4: User Story 2 — Interactive Price and Volume Trend Exploration (Priority: P2)

**Goal**: An energy analyst explores multi-year trends via interactive charts with region and time-range filters, tooltips, and a volume aggregation toggle.

**Independent Test**: Open dashboard with pre-seeded multi-year data. Verify: price line chart displays, volume chart displays with per-auction data points, region filter updates charts within 2 seconds, hover tooltips show exact values, aggregation toggle switches between per-auction/monthly/yearly.

### Backend Endpoints for US2

- [X] T034 [P] [US2] Implement GET /api/v1/charts/prices endpoint in `src/backend/app/api/stats.py` — query Auction table where status='past' and technology IS NULL, support start_date (default: 5 years ago), end_date (default: today), region, technology filters. Return list of {auction_date, region, weighted_avg_price_eur, volume_allocated_mwh} ordered by auction_date ASC. Include applied filters in response
- [X] T035 [P] [US2] Implement GET /api/v1/charts/volumes endpoint in `src/backend/app/api/stats.py` — query Auction table where status='past' and technology IS NULL, support start_date, end_date, region, technology, aggregation (per_auction/monthly/yearly). For per_auction: return individual data points. For monthly/yearly: GROUP BY truncated period, SUM volumes. Return {period, region, volume_offered_mwh, volume_allocated_mwh}. Include applied filters in response
- [X] T036 [P] [US2] Implement GET /api/v1/technologies endpoint in `src/backend/app/api/auctions.py` — query DISTINCT technology from Auction table where technology IS NOT NULL, ordered alphabetically. Return list of technology names

### Frontend Components for US2

- [X] T037 [P] [US2] Create RegionFilter component in `src/frontend/src/components/RegionFilter.vue` — dropdown/select populated from GET /api/v1/regions with "All Regions" default option. Emit region-change event. Keyboard-accessible with ARIA attributes. Responsive
- [X] T038 [P] [US2] Create PriceChart component in `src/frontend/src/components/PriceChart.vue` — ECharts line chart (via vue-echarts) showing weighted_avg_price_eur on y-axis, auction_date on x-axis. Configure: responsive resize, tooltip on hover showing date + price + region (FR-011), zoom/pan for exploration, grid lines, axis labels. Use EEX green accent for line colour. Use modular ECharts imports (LineChart, TooltipComponent, GridComponent, DataZoomComponent) for tree-shaking
- [X] T039 [P] [US2] Create VolumeChart component in `src/frontend/src/components/VolumeChart.vue` — ECharts bar/scatter chart showing volume_allocated_mwh on y-axis, period on x-axis. Default to per-auction discrete data points (scatter). Include toggle control (buttons or dropdown) for per_auction/monthly/yearly aggregation (FR-009). Tooltip on hover showing date + offered + allocated volumes + region. Responsive resize. Use modular ECharts imports
- [X] T040 [US2] Create useChartData composable in `src/frontend/src/composables/useChartData.ts` — reactive state for price data, volume data, active filters (region, startDate, endDate, aggregation). Functions to fetch chart endpoints with current filters. Debounced filter application for smooth UX. Loading states per chart
- [X] T041 [US2] Integrate charts into dashboard layout in `src/frontend/src/App.vue` — add charts section below the overview section. Shared RegionFilter and DateRangeFilter that update both charts simultaneously (FR-010, FR-012). Aggregation toggle only on VolumeChart. Charts update dynamically without page reload. Lazy-load chart components for faster initial render

**Checkpoint**: Interactive charts fully functional. Price and volume trends visible over multi-year history. Region filter updates both charts within 2 seconds. Tooltips display exact values. Volume aggregation toggle works. All testable with pre-seeded database.

---

## Phase 5: User Story 3 — Automatic Data Synchronisation (Priority: P3)

**Goal**: The system automatically fetches new auction results and calendar updates from EEX daily, with a manual CLI trigger and historical backfill capability.

**Independent Test**: Run `python -m app.services.sync --manual` against a mocked EEX data source containing a new auction result. Verify: result appears in database, "Last updated" timestamp advances. Run `--backfill` and verify historical records appear.

### Backend Sync Implementation

- [X] T042 [US3] Implement Excel/ZIP parser service in `src/backend/app/services/parser.py` — functions to: extract ZIP to temp directory, parse each .xlsx file using openpyxl (detect header row by scanning for known column names like "Region", "Volume Offered", "Weighted Average Price"; map columns dynamically), convert each data row to an Auction dict. Run openpyxl operations in a thread pool executor (asyncio.to_thread) to avoid blocking the event loop. Log warnings for unrecognised column layouts. Handle missing fields gracefully (store as NULL)
- [X] T043 [US3] Implement HTML scraper for latest results in `src/backend/app/services/parser.py` — async function using httpx to fetch the EEX auctions page, parse HTML to extract the latest auction results tables (by Region and by Technology). Extract auction_date, production_period from page context. Return list of Auction dicts. Log descriptive errors if expected HTML elements not found
- [X] T044 [US3] Implement HTML scraper for auction calendar in `src/backend/app/services/parser.py` — async function to parse the calendar table from the EEX page. Extract rows with: auction_date, production_period, order_book_open, order_book_close, order_matching. Return list of Auction dicts with status='upcoming'. Log descriptive errors if calendar structure changes
- [X] T045 [US3] Implement sync orchestrator service in `src/backend/app/services/sync.py` — main SyncService class with methods: `run_backfill()` — discover ZIP URLs from EEX downloads page, download each to `data/downloads/` (skip if cached), extract and parse all Excel files via parser, upsert records using composite key (fill NULL fields, never overwrite non-NULL). `run_daily()` — scrape latest results and calendar from HTML, upsert result records, create/update upcoming auction records, transition upcoming→past when results found, remove upcoming records that disappeared from calendar. `run_manual()` — alias for run_daily(). All methods: create SyncLog entry at start, update with outcome/counts at end. On failure: log error, preserve existing data, do not update SyncLog to success (FR-017)
- [X] T046 [US3] Implement CLI entry point for manual sync in `src/backend/app/services/sync.py` — add `if __name__ == "__main__"` or use argparse/click: `python -m app.services.sync --backfill` for full historical backfill, `python -m app.services.sync --manual` for daily incremental sync. Print summary (records added/updated/skipped) on completion. Exit code 0 on success, 1 on failure. FR-020: this is CLI-only, NOT exposed as HTTP endpoint
- [X] T047 [US3] Integrate APScheduler into FastAPI application in `src/backend/app/main.py` — add AsyncIOScheduler in lifespan handler. Schedule daily sync job at configured hour/minute (from config.py). Only start scheduler if SYNC_ENABLED=true. Log scheduler start/stop. Ensure scheduler shuts down cleanly on app exit

**Checkpoint**: Sync system fully operational. Backfill downloads and parses all historical ZIP archives. Daily sync fetches latest results and calendar. Manual CLI trigger works. SyncLog records each run. "Last updated" timestamp reflects latest successful sync on dashboard.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories — responsiveness, accessibility, caching, health check.

- [X] T048 [P] Add GET /api/v1/health endpoint in `src/backend/app/api/router.py` — return `{"status": "ok", "database": "connected"}` when DB reachable, `{"status": "degraded", "database": "unreachable"}` with 503 when not
- [X] T049 [P] Add Cache-Control headers to API responses in `src/backend/app/middleware/security.py` — `/api/v1/regions` and `/api/v1/technologies`: `Cache-Control: public, max-age=86400` (1 day). `/api/v1/stats`, `/api/v1/charts/*`: `Cache-Control: public, max-age=3600` (1 hour). `/api/v1/auctions`, `/api/v1/auctions/upcoming`: `Cache-Control: public, max-age=300` (5 min). `/api/v1/health`: `Cache-Control: no-store`
- [X] T050 [P] Verify responsive design across all components in `src/frontend/src/` — test at 320px, 768px, 1024px, 1920px widths. Ensure no horizontal scrolling, tables convert to card layout on mobile, charts resize, filter controls stack vertically on small screens (FR-007)
- [X] T051 [P] Add ARIA attributes and keyboard navigation to all interactive components in `src/frontend/src/components/` — RegionFilter, DateRangeFilter, aggregation toggle, table sort controls must be keyboard-navigable with appropriate `aria-label`, `role`, and `aria-live` attributes for dynamic content updates (Constitution IV)
- [X] T052 Validate full quickstart.md flow end-to-end — follow every step in `specs/001-pgo-auctions-dashboard/quickstart.md` from clone through backfill, verify dashboard displays data. Confirm all quality gates pass (ruff, mypy, pytest, eslint, vue-tsc, vitest). Fix any issues found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) completion
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) completion. Shares RegionFilter and DateRangeFilter with US1 but can be developed independently
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) completion. Independent of US1/US2 frontend but writes data that US1/US2 display
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Start after Phase 2. No dependency on other stories. MVP milestone.
- **US2 (P2)**: Start after Phase 2. Reuses RegionFilter and DateRangeFilter from US1 — if developing in parallel, extract shared components in Phase 2 or coordinate.
- **US3 (P3)**: Start after Phase 2. Fully independent backend work. Can be developed in parallel with US1/US2.

### Within Each User Story

- Backend endpoints before frontend components (frontend needs API to call)
- Models and schemas are in Foundational phase (shared)
- Frontend composables before components that consume them
- Integration/assembly task last in each phase

### Parallel Opportunities

**Phase 1**: T003, T004, T005, T006 can all run in parallel after T001-T002.

**Phase 2**: T009+T010 (models) in parallel; T015+T016 (middleware) in parallel; T019+T020 (frontend) in parallel; T053+T054+T055 (foundational tests) in parallel.

**Phase 3 (US1)**: T025+T026 (stats+regions endpoints) in parallel; T027-T031 (all frontend components) in parallel.

**Phase 4 (US2)**: T034+T035+T036 (all chart endpoints) in parallel; T037+T038+T039 (all chart components) in parallel.

**Phase 6**: T048+T049+T050+T051 all in parallel.

---

## Parallel Example: User Story 1

```text
# Backend endpoints — launch in parallel:
T025: Implement GET /api/v1/stats in src/backend/app/api/stats.py
T026: Implement GET /api/v1/regions in src/backend/app/api/auctions.py

# Frontend components — launch in parallel:
T027: Create AuctionTable in src/frontend/src/components/AuctionTable.vue
T028: Create DateRangeFilter in src/frontend/src/components/DateRangeFilter.vue
T029: Create UpcomingAuctions in src/frontend/src/components/UpcomingAuctions.vue
T030: Create StatsPanel in src/frontend/src/components/StatsPanel.vue
T031: Create LastUpdated in src/frontend/src/components/LastUpdated.vue
```

## Parallel Example: User Story 2

```text
# Backend endpoints — launch in parallel:
T034: Implement GET /api/v1/charts/prices in src/backend/app/api/stats.py
T035: Implement GET /api/v1/charts/volumes in src/backend/app/api/stats.py
T036: Implement GET /api/v1/technologies in src/backend/app/api/auctions.py

# Frontend components — launch in parallel:
T037: Create RegionFilter in src/frontend/src/components/RegionFilter.vue
T038: Create PriceChart in src/frontend/src/components/PriceChart.vue
T039: Create VolumeChart in src/frontend/src/components/VolumeChart.vue
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — Auction Dashboard Overview
4. **STOP and VALIDATE**: Seed database manually, verify dashboard shows past auctions, upcoming, stats, last-updated
5. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Validate → Deploy/Demo (**MVP**)
3. Add User Story 2 → Validate charts → Deploy/Demo
4. Add User Story 3 → Validate sync → Deploy/Demo (self-maintaining system)
5. Polish phase → Production-ready

### Parallel Team Strategy

With multiple developers after Foundational completes:
- **Developer A**: User Story 1 (backend endpoints + frontend components)
- **Developer B**: User Story 3 (sync service — entirely backend, no frontend overlap)
- **Developer C**: User Story 2 (chart endpoints + chart components)
- Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [US1/US2/US3] labels map tasks to specific user stories for traceability
- Each user story is independently completable and testable with a pre-seeded database
- Commit after each task or logical group — all quality gates must pass (Constitution II)
- Stop at any checkpoint to validate the story independently
- All backend Python: PEP 8, double quotes, async-first, structlog logging
- All frontend Vue: Composition API, TypeScript strict, business logic in composables not templates
