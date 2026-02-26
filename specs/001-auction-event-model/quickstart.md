# Quickstart: AuctionEvent Feature Development

**Branch**: `001-auction-event-model`

## Prerequisites

- Python virtual environment activated: `source src/backend/.venv/Scripts/activate` (Windows)
- PostgreSQL running and `.env` configured with `DATABASE_URL`

---

## 1. Run the new Alembic migration

```bash
cd src/backend
alembic upgrade head
```

This applies `002_add_auction_event.py`:
- Creates the `auction_event` table
- Adds `auction_event_id` FK column to `auction`

---

## 2. Run a daily sync to populate AuctionEvents

```bash
cd src/backend
python -m app.services.sync --manual
```

This triggers `run_manual()` → `run_daily()`, which now also:
1. Scrapes EEX calendar for auction events
2. Upserts `AuctionEvent` records (create/update by `event_date`)
3. Links `Auction` records to their events via `auction_event_id`
4. Marks events that vanished from the calendar as `is_cancelled = True`

Expected output:
```
Starting manual incremental sync…
Sync complete — added: X, updated: Y, skipped: Z
AuctionEvents synced: A added, B updated, C cancelled
```

---

## 3. Query the new API endpoint

With the backend running (`uvicorn app.main:app --reload --port 8000`):

```bash
# All events (upcoming + completed)
curl http://localhost:8000/api/v1/auction-events

# Only upcoming events
curl "http://localhost:8000/api/v1/auction-events?start_date=$(date +%Y-%m-%d)"

# Include cancelled events
curl "http://localhost:8000/api/v1/auction-events?include_cancelled=true"
```

---

## 4. Run quality gates

```bash
cd src/backend

# Lint
ruff check .

# Type check
mypy app/

# Tests
pytest tests/ -v
```

All three must pass before committing.

---

## Key files changed

| File | Change |
|---|---|
| `app/models/auction_event.py` | **NEW** — AuctionEvent SQLAlchemy model |
| `app/models/auction.py` | **MODIFIED** — add `auction_event_id` FK + relationship |
| `app/schemas/auction_event.py` | **NEW** — Pydantic response schemas |
| `app/api/auction_events.py` | **NEW** — `GET /api/v1/auction-events` endpoint |
| `app/api/router.py` | **MODIFIED** — register auction_events router |
| `app/services/parser.py` | **MODIFIED** — add `scrape_auction_events()` |
| `app/services/sync.py` | **MODIFIED** — integrate event sync into `run_daily()` |
| `alembic/versions/002_add_auction_event.py` | **NEW** — schema migration |
| `tests/unit/test_auction_event_sync.py` | **NEW** — sync unit tests |
| `tests/unit/test_auction_event_api.py` | **NEW** — API unit tests |
| `src/frontend/src/components/AuctionEventList.vue` | **NEW** — Vue component |
