# Tasks: AuctionEvent Model

**Input**: Design documents from `specs/001-auction-event-model/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅ | quickstart.md ✅

**Tests**: Included — test files are explicitly specified in plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm project is ready for feature work. No new tooling required — project is
already initialized with Alembic, SQLAlchemy, FastAPI, Vue, and pytest.

- [x] T001 Confirm alembic migration chain has no uncommitted head in `src/backend/alembic/versions/` before writing new migration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data layer changes that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 Create `AuctionEvent` SQLAlchemy ORM model with `event_date` (UNIQUE Date), `is_cancelled` (Boolean), `created_at`/`updated_at` timestamps, and `auctions` relationship in `src/backend/app/models/auction_event.py`
- [x] T003 Add `auction_event_id` nullable FK column (`ForeignKey("auction_event.id")`) and `auction_event` back-reference relationship to `Auction` in `src/backend/app/models/auction.py`; add `Index("idx_auction_event_id", "auction_event_id")` to `__table_args__`
- [x] T004 [P] Export `AuctionEvent` from `src/backend/app/models/__init__.py` alongside existing exports
- [x] T005 Write Alembic migration `002_add_auction_event` in `src/backend/alembic/versions/002_add_auction_event.py`: `upgrade()` creates `auction_event` table (all columns, PK, UNIQUE constraint, `idx_auction_event_cancelled` index) then adds `auction_event_id` column + FK constraint + `idx_auction_event_id` index to `auction`; `downgrade()` reverses all steps in order

**Checkpoint**: Run `alembic upgrade head` — both tables reflect the new schema. No data loss on existing rows.

---

## Phase 3: User Story 1 — View Auction Events in Dashboard (Priority: P1) 🎯 MVP

**Goal**: Expose a `GET /api/v1/auction-events` endpoint that returns AuctionEvents with
their associated auctions; display the list in a new Vue component.

**Independent Test**: Seed two AuctionEvents (one with auctions, one empty) directly in
the test database. Call `GET /api/v1/auction-events` and verify both appear with correct
`status`, `is_cancelled`, and nested `auctions` arrays. Open the dashboard and confirm the
`AuctionEventList` component renders without errors.

### Tests for User Story 1

- [x] T006 [P] [US1] Write unit tests covering `list_auction_events` endpoint (seeded data, status computation, pagination of auctions, 400 on invalid date) in `src/backend/tests/unit/test_auction_event_api.py`
- [x] T007 [P] [US1] Write Vitest component tests for `AuctionEventList.vue` (renders event list, shows event date, renders nested auction rows) in `src/frontend/src/__tests__/AuctionEventList.spec.ts`

### Implementation for User Story 1

- [x] T008 [US1] Create Pydantic schemas `AuctionSummary`, `AuctionEventResponse` (with computed `status` field), and `AuctionEventListResponse` in `src/backend/app/schemas/auction_event.py`
- [x] T009 [US1] Implement `GET /api/v1/auction-events` FastAPI endpoint with `include_cancelled` (bool, default `false`), `start_date`, `end_date` query params; compute `status` from `event_date` vs `date.today()`; load `auctions` via `selectinload(AuctionEvent.auctions)`; sort by `event_date` descending in `src/backend/app/api/auction_events.py`
- [x] T010 [US1] Register the new `auction_events.router` under the `/api/v1` prefix in `src/backend/app/api/router.py`
- [x] T011 [P] [US1] Create typed `getAuctionEvents(params)` API client function with `AuctionEventRecord` / `AuctionEventListResponse` types in `src/frontend/src/services/api.ts`
- [x] T012 [US1] Create `AuctionEventList.vue` component that calls `fetchAuctionEvents`, renders a list of events each showing event date and a nested table of associated auctions (region, production period, technology); mobile-responsive layout 320–1920 px in `src/frontend/src/components/AuctionEventList.vue`

**Checkpoint**: `GET /api/v1/auction-events` returns data; `AuctionEventList.vue` renders
the list in the browser. Lint, mypy, and pytest for US1 tests are all green.

---

## Phase 4: User Story 2 — Automatic Data Synchronization from EEX Calendar (Priority: P2)

**Goal**: Integrate AuctionEvent upsert (create/update/cancel) into `run_daily()` so
every scheduled sync keeps AuctionEvent records in sync with the EEX calendar.

**Independent Test**: Mock the EEX HTTP response in unit tests. Call `run_daily()` (or the
new sync methods directly). Assert: (a) new AuctionEvents are created; (b) re-running with
the same data creates no duplicates; (c) a date removed from the mock calendar sets
`is_cancelled = True` on the corresponding AuctionEvent; (d) existing `Auction` records
for that date get their `auction_event_id` populated.

### Tests for User Story 2

- [x] T013 [P] [US2] Write unit tests covering `_upsert_auction_event` (add new, skip existing), `_bulk_upsert_auction_events` (dedup), `_link_auctions_to_events` (FK set on matching Auction rows), `_mark_cancelled_events` (flag vanished dates; ignore past dates) in `src/backend/tests/unit/test_auction_event_sync.py`

### Implementation for User Story 2

- [x] T014 [US2] Add async `scrape_auction_events(eex_base_url, http_client)` to `src/backend/app/services/parser.py`; reuse existing `_extract_table_rows` and calendar column-matching logic; return `list[dict]` with one `{"event_date": date, "is_cancelled": False}` entry per unique future `event_date` found in the EEX calendar table
- [x] T015 [US2] Add `_upsert_auction_event(session, event_date)` → `"added" | "skipped"` and `_bulk_upsert_auction_events(session, event_dates)` → `(added, skipped)` methods to `SyncService` in `src/backend/app/services/sync.py`
- [x] T016 [P] [US2] Add `_link_auctions_to_events(session)` → `int` method to `SyncService` that sets `auction_event_id` on `Auction` rows where `auction_date` matches an existing `AuctionEvent.event_date` and `auction_event_id` is still NULL in `src/backend/app/services/sync.py`
- [x] T017 [P] [US2] Add `_mark_cancelled_events(session, live_event_dates)` → `int` method to `SyncService` that sets `is_cancelled = True` on `AuctionEvent` rows whose `event_date >= today` no longer appears in `live_event_dates`; add structlog entries for `events_cancelled` count in `src/backend/app/services/sync.py`
- [x] T018 [US2] Integrate AuctionEvent sync into `run_daily()` in `src/backend/app/services/sync.py`: after existing steps 1–6, call `scrape_auction_events`, then `_bulk_upsert_auction_events`, then `_link_auctions_to_events`, then `_mark_cancelled_events`; log `auction_events_synced` with added/skipped/cancelled counts; wrap in same failure-safe pattern as existing steps (FR-008: exception must not corrupt existing data)

**Checkpoint**: `python -m app.services.sync --manual` logs `auction_events_synced` with
nonzero counts. Re-running logs zero `added`, zero `cancelled`. All US2 unit tests pass.

---

## Phase 5: User Story 3 — Historical and Future Auction Event Visibility (Priority: P3)

**Goal**: Visually distinguish upcoming vs. completed events in the dashboard; show a clear
"Cancelled" label on events marked `is_cancelled`.

**Independent Test**: Seed one upcoming AuctionEvent (future date), one completed
AuctionEvent (past date), and one cancelled AuctionEvent. Open the dashboard and verify:
(a) upcoming event has a visible "Upcoming" badge; (b) completed event has a "Completed"
badge; (c) cancelled event is hidden by default and shows a "Cancelled" label when
`include_cancelled=true` is active.

### Tests for User Story 3

- [x] T019 [P] [US3] Extend `src/frontend/tests/unit/AuctionEventList.spec.ts` with tests: future `event_date` → "Upcoming" badge rendered; past `event_date` → "Completed" badge rendered; `is_cancelled=true` → "Cancelled" label rendered; cancelled event excluded when `include_cancelled=false`

### Implementation for User Story 3

- [x] T020 [US3] Add `status` badge display (green "Upcoming" / grey "Completed") and "Cancelled" label (red) to each event card in `src/frontend/src/components/AuctionEventList.vue`; cancelled events visually distinct but not hidden (toggled by a UI control that calls `fetchAuctionEvents({ include_cancelled: true })`)
- [x] T021 [P] [US3] Add "Show cancelled" toggle control to `AuctionEventList.vue` that re-fetches with `include_cancelled=true|false`; keep responsive layout (320–1920 px)

**Checkpoint**: Dashboard correctly labels all three event states. Toggling "Show cancelled"
fetches and renders cancelled events with the label. US3 Vitest tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gate sign-off and end-to-end validation before PR.

- [x] T022 Run `ruff check src/backend/` and resolve all lint errors; run `mypy src/backend/app/` and resolve all type errors across all new and modified files
- [x] T023 [P] Run full pytest suite `pytest src/backend/tests/ -v` and confirm zero failures or unexplained skips
- [x] T024 [P] Run `quickstart.md` end-to-end scenario: apply migration → run `--manual` sync → query `GET /api/v1/auction-events` → verify events appear with correct structure
- [x] T025 [P] Run ESLint on `src/frontend/` and Vitest full suite; confirm zero errors

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    └── Phase 2 (Foundational)  ← BLOCKS all user stories
            ├── Phase 3 (US1 — P1)
            ├── Phase 4 (US2 — P2)
            └── Phase 5 (US3 — P3)  ← depends on Phase 3 frontend work
                        └── Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depends On | Notes |
|---|---|---|
| US1 (P1) — View Dashboard | Phase 2 only | Can be seeded with test data; no US2 sync required for testing |
| US2 (P2) — Data Sync | Phase 2 only | Backend only; independent of US1 |
| US3 (P3) — Status Display | US1 frontend component (T012) | Extends the AuctionEventList component from US1 |

### Within Each User Story

- Tests (T006, T007, T013, T019) MUST be written before implementation; verify they fail
- Models/schemas before endpoints
- Endpoints before frontend components
- Story complete and all tests green before moving to next story

### Parallel Opportunities

- After T002 completes: T003, T004, T005 can all run in parallel
- After Phase 2: US1 and US2 can be worked in parallel (different files throughout)
- Within US1: T006, T007, T011 are all [P] and can start simultaneously
- Within US2: T013 can start as soon as Phase 2 is done; T016 and T017 are [P] after T015

---

## Parallel Example: User Story 1

```
# Launch all US1 test and frontend tasks in parallel (after T008 schemas are done):
Task: T006 — Write test_auction_event_api.py
Task: T007 — Write AuctionEventList.spec.ts
Task: T011 — Write auctionEvents.ts API client

# Then launch implementation tasks (after T009 endpoint is done):
Task: T012 — Build AuctionEventList.vue
```

## Parallel Example: User Story 2

```
# Start test writing immediately (after Phase 2):
Task: T013 — Write test_auction_event_sync.py

# Parser and sync methods are independent of each other initially:
Task: T014 — Add scrape_auction_events() to parser.py
Task: T015 — Add _upsert methods to sync.py  [after T014]
Task: T016 — Add _link_auctions_to_events()  [P, after T015]
Task: T017 — Add _mark_cancelled_events()    [P, after T015]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T005) — CRITICAL, blocks everything
3. Complete Phase 3: US1 (T006–T012)
4. **STOP and VALIDATE**: query `GET /api/v1/auction-events` with seeded data; verify Vue component renders
5. Deploy/demo if ready — the endpoint and UI exist even before live EEX sync is wired up

### Incremental Delivery

1. Setup + Foundational → schema ready
2. US1 (View) → dashboard endpoint + component live (testable with seeded data)
3. US2 (Sync) → real EEX data starts flowing into AuctionEvents
4. US3 (Status Display) → upcoming/completed/cancelled labels polished
5. Polish → PR-ready

### Parallel Team Strategy

With two developers after Phase 2:
- **Dev A**: US1 (T006–T012) — API schemas, endpoint, router, Vue component
- **Dev B**: US2 (T013–T018) — parser function, sync service methods, run_daily integration

---

## Notes

- [P] tasks operate on different files — no conflicts
- [Story] label maps each task to spec.md user stories for traceability
- `auction_event_id` is nullable — no data migration required; existing rows unaffected
- The `is_cancelled` flag replaces deletion — never use `DELETE` on AuctionEvent records
- Always run lint + mypy + tests before marking any task complete (Constitution II)
- Commit after each logical group; do not batch unrelated changes
