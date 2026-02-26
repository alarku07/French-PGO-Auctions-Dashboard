# Implementation Plan: AuctionEvent Model

**Branch**: `001-auction-event-model` | **Date**: 2026-02-25 | **Spec**: `specs/001-auction-event-model/spec.md`
**Input**: Feature specification from `specs/001-auction-event-model/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add an `AuctionEvent` model that groups individual auctions occurring on the same calendar
date, sourced from the EEX French Auctions Calendar. Integrate automated upsert of
AuctionEvent records into the existing `run_daily()` / `run_manual()` sync pipeline.
Expose a new `GET /api/v1/auction-events` endpoint for the dashboard. Cancelled events
(removed from EEX) are retained and flagged, never deleted.

---

## Technical Context

**Language/Version**: Python 3.13 (latest stable; confirmed via `.mypy_cache/3.13/`)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, httpx, BeautifulSoup4, structlog, Alembic, Pydantic v2
**Storage**: PostgreSQL (production/development); SQLite permitted for local POC only
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server
**Project Type**: web-service (Python backend + Vue.js frontend)
**Performance Goals**: SC-004 — users view any AuctionEvent and its auctions in < 3 seconds
**Constraints**: Zero data loss; FK column nullable so no data migration required; cancelled events retained forever
**Scale/Scope**: Tens to low hundreds of AuctionEvents per year; no high-throughput concerns

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|---|---|---|---|
| I. Data Integrity | AuctionEvents MUST NOT be deleted | ✅ PASS | `is_cancelled` flag used; no DELETE |
| I. Data Integrity | New migration is additive only | ✅ PASS | Add table + nullable FK; existing rows unaffected |
| I. Data Integrity | PostgreSQL required for development | ✅ PASS | No deviation from stack |
| II. Quality Gates | Lint (ruff/flake8), type check (mypy), unit tests all green before merge | ✅ PASS | Enforced per all tasks |
| III. Python Discipline | Async-first (`AsyncSession`, `httpx`) | ✅ PASS | All new code follows async pattern |
| III. Python Discipline | Double quotes, PEP 8, venv | ✅ PASS | No deviations planned |
| IV. Frontend Standards | New Vue component responsive 320–1920 px | ✅ PASS | `AuctionEventList.vue` scoped to mobile-first |
| V. Observability | Sync outcome logged (FR-007) | ✅ PASS | structlog entries for events added/updated/cancelled |

**Post-design re-check**: No violations found. The `_remove_vanished_calendar_entries()`
behavior change (retain instead of delete) aligns with Principle I.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-auction-event-model/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
  backend/
    app/
      models/
        auction_event.py        # NEW: AuctionEvent SQLAlchemy model
        auction.py              # MODIFIED: auction_event_id FK + relationship
        __init__.py             # MODIFIED: export AuctionEvent
      schemas/
        auction_event.py        # NEW: Pydantic schemas (AuctionEventResponse etc.)
      api/
        auction_events.py       # NEW: GET /api/v1/auction-events
        router.py               # MODIFIED: include auction_events router
      services/
        parser.py               # MODIFIED: add scrape_auction_events()
        sync.py                 # MODIFIED: integrate event sync into run_daily()
    alembic/
      versions/
        002_add_auction_event.py  # NEW: additive migration
    tests/
      unit/
        test_auction_event_sync.py   # NEW: sync unit tests
        test_auction_event_api.py    # NEW: API endpoint unit tests

  frontend/
    src/
      components/
        AuctionEventList.vue    # NEW: displays grouped auction events
      api/
        auctionEvents.ts        # NEW: typed API client for /auction-events
    tests/
      unit/
        AuctionEventList.spec.ts  # NEW: Vitest component tests
```

**Structure Decision**: Web application layout (Option 2). Backend under `src/backend/`,
frontend under `src/frontend/`. Follows existing project conventions exactly.

---

## Implementation Guide

### Phase A — Data Layer

#### 1. New model: `app/models/auction_event.py`

```python
class AuctionEvent(Base):
    __tablename__ = "auction_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)

    auctions: Mapped[list["Auction"]] = relationship(
        "Auction", back_populates="auction_event", cascade="save-update"
    )

    __table_args__ = (
        UniqueConstraint("event_date", name="uq_auction_event_date"),
        Index("idx_auction_event_cancelled", "is_cancelled"),
    )
```

#### 2. Modify `app/models/auction.py`

Add to `Auction`:
```python
auction_event_id: Mapped[int | None] = mapped_column(
    Integer, ForeignKey("auction_event.id"), nullable=True
)
auction_event: Mapped["AuctionEvent | None"] = relationship(
    "AuctionEvent", back_populates="auctions"
)
```
Add `Index("idx_auction_event_id", "auction_event_id")` to `__table_args__`.

#### 3. New Alembic migration: `002_add_auction_event.py`

- `upgrade()`: create `auction_event` table; add nullable `auction_event_id` column +
  FK constraint + index to `auction`.
- `downgrade()`: reverse all steps (drop FK, column, index, table).

---

### Phase B — Parser

#### 4. Add `scrape_auction_events()` to `app/services/parser.py`

New async function that fetches the same EEX page as `scrape_auction_calendar()` and
returns a list of event-shaped dicts:

```python
async def scrape_auction_events(
    eex_base_url: str,
    http_client: httpx.AsyncClient,
) -> list[dict[str, Any]]:
    """
    Returns list of dicts: {"event_date": date, "is_cancelled": False}
    One entry per unique event_date found in the calendar table.
    """
```

Implementation notes:
- Reuse `_extract_table_rows()` and the calendar column-matching logic from
  `scrape_auction_calendar()`.
- Deduplicate by `event_date` (calendar may list same date in multiple production-period rows).
- Only include future dates (calendar is forward-looking; past events are retained in DB
  but not on the EEX page).

---

### Phase C — Sync Service

#### 5. Modify `app/services/sync.py`

**New methods on `SyncService`:**

```python
async def _upsert_auction_event(
    self, session: AsyncSession, event_date: date
) -> str:
    """Upsert one AuctionEvent by event_date. Returns 'added' | 'skipped'."""

async def _bulk_upsert_auction_events(
    self, session: AsyncSession, event_dates: list[date]
) -> tuple[int, int]:
    """Upsert all AuctionEvents. Returns (added, skipped)."""

async def _link_auctions_to_events(
    self, session: AsyncSession
) -> int:
    """
    For each AuctionEvent, set auction_event_id on matching Auction records
    (where Auction.auction_date == AuctionEvent.event_date and
    Auction.auction_event_id IS NULL).
    Returns number of links created.
    """

async def _mark_cancelled_events(
    self, session: AsyncSession, live_event_dates: set[date]
) -> int:
    """
    Mark AuctionEvents as cancelled when their event_date is no longer
    returned by the EEX calendar scraper.
    Only marks events with event_date >= today (past events are expected
    to not appear in the live calendar).
    Returns number of events newly cancelled.
    """
```

**Modified `run_daily()`** — add after steps 1–6:

```python
# 7. Scrape and upsert AuctionEvents
event_records = await scrape_auction_events(self._eex_base_url, http_client)
event_dates = [r["event_date"] for r in event_records]

async with session_factory() as session:
    ev_added, ev_skipped = await self._bulk_upsert_auction_events(session, event_dates)
    links_created = await self._link_auctions_to_events(session)
    cancelled = await self._mark_cancelled_events(
        session, set(event_dates)
    )
    await session.commit()

logger.info(
    "auction_events_synced",
    added=ev_added, skipped=ev_skipped,
    links=links_created, cancelled=cancelled,
)
```

**Refactor `_remove_vanished_calendar_entries()`**: This method currently deletes
upcoming `Auction` records. With AuctionEvents in place, the cancellation is handled at
the event level by `_mark_cancelled_events()`. The old method should remain for now
(it cleans up calendar-only upcoming Auction rows that never had an AuctionEvent parent),
but its interaction with the new cancellation logic must be verified in tests.

---

### Phase D — API + Schemas

#### 6. New schemas: `app/schemas/auction_event.py`

```python
class AuctionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    auction_date: date
    region: str
    production_period: str
    technology: str | None
    status: str

class AuctionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_date: date
    status: str           # computed: "upcoming" | "completed"
    is_cancelled: bool
    auctions: list[AuctionSummary]

class AuctionEventListResponse(BaseModel):
    data: list[AuctionEventResponse]
    count: int
```

`status` is computed in the endpoint from `event_date` vs `date.today()`.

#### 7. New endpoint: `app/api/auction_events.py`

```python
@router.get("/auction-events", response_model=AuctionEventListResponse)
async def list_auction_events(
    include_cancelled: bool = Query(False),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> AuctionEventListResponse:
    stmt = (
        select(AuctionEvent)
        .options(selectinload(AuctionEvent.auctions))
        .order_by(AuctionEvent.event_date.desc())
    )
    if not include_cancelled:
        stmt = stmt.where(AuctionEvent.is_cancelled.is_(False))
    if start_date:
        stmt = stmt.where(AuctionEvent.event_date >= _parse_date(start_date, ...))
    if end_date:
        stmt = stmt.where(AuctionEvent.event_date <= _parse_date(end_date, ...))
    ...
```

#### 8. Register in `app/api/router.py`

Include the new `auction_events.router` under the `/api/v1` prefix.

---

### Phase E — Frontend

#### 9. New Vue component: `AuctionEventList.vue`

Displays a list of AuctionEvents grouped by status (upcoming / completed).
Each event shows:
- Event date
- Status badge (upcoming / completed)
- Cancelled badge when `is_cancelled = true`
- Collapsible list of associated auctions (region, technology, production period)

Must render correctly from 320 px to 1920 px (constitution Principle IV).

#### 10. API client: `src/frontend/src/api/auctionEvents.ts`

Typed fetch wrapper for `GET /api/v1/auction-events`.

---

### Phase F — Tests

#### 11. `tests/unit/test_auction_event_sync.py`

| Test | Covers |
|---|---|
| `test_upsert_creates_new_event` | New date → AuctionEvent inserted |
| `test_upsert_skips_existing_event` | Duplicate date → no duplicate created (SC-005) |
| `test_mark_cancelled_flags_vanished_event` | Date removed from calendar → `is_cancelled = True` |
| `test_mark_cancelled_ignores_past_events` | Past dates not on live calendar → not cancelled |
| `test_link_auctions_to_events` | Auction.auction_date matches event → FK set |
| `test_graceful_failure_preserves_data` | Exception during event sync → existing data unchanged (FR-008) |

#### 12. `tests/unit/test_auction_event_api.py`

| Test | Covers |
|---|---|
| `test_list_events_returns_events` | Endpoint returns seeded AuctionEvents |
| `test_status_computed_from_date` | Future date → `upcoming`; past date → `completed` |
| `test_cancelled_excluded_by_default` | Cancelled events hidden unless `include_cancelled=true` |
| `test_cancelled_included_when_requested` | `include_cancelled=true` → cancelled events returned |
| `test_auctions_nested_in_event` | Associated Auction records appear in `auctions` array |

---

## Complexity Tracking

No constitution violations. No complexity justification required.
