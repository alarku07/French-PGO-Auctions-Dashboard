# Research: AuctionEvent Model — Data Sync Integration

**Branch**: `001-auction-event-model` | **Phase**: Phase 0

## EEX Calendar Page Structure

### Decision: One calendar row = one AuctionEvent

**Decision**: Each row in the EEX French Auctions Power "Calendar" table represents one
auction event — a single auction session scheduled for a specific date. The `AuctionEvent`
entity maps directly to one calendar row.

**Rationale**: The calendar table exposes these columns:

| Column (variants) | Meaning |
|---|---|
| Auctioning Month / Auction Date | Date the auction session occurs (`event_date`) |
| Production Month / Production Period | Month/year the GOs relate to (not the event date) |
| Order Book Opening | When bidding opens |
| Order Book Closure | When bidding closes |
| Order Matching | When winners are determined |

One row per event date; no per-region or per-technology breakdown in the calendar. The
breakdown appears only in the results table (after the auction settles).

**Alternatives considered**:
- One AuctionEvent per production period — rejected; the spec uniquely identifies events
  by calendar date, not production period. Multiple sessions can cover different production
  months but happen on distinct dates.

---

## Relationship Design: FK vs. Derived Join

### Decision: Explicit `auction_event_id` FK on `Auction`

**Decision**: Add a nullable integer column `auction_event_id` as a FK on the `auction`
table pointing to `auction_event.id`.

**Rationale**:
- DB-enforced referential integrity; no silent mismatches.
- SQLAlchemy `relationship()` requires a real FK for standard ORM navigation.
- Easier to index and query than a `primaryjoin` expression on matching dates.
- Future-proof: if AuctionEvent ever gets additional natural-key fields, the FK stays stable.

**Alternatives considered**:
- `primaryjoin` on `Auction.auction_date == AuctionEvent.event_date` — fragile, no DB
  constraint, hard to type-check. Rejected.
- Association table `auction_event_auctions` — unnecessary indirection; the relationship
  is already one-to-many. Rejected.

---

## SQLAlchemy Relationship Pattern

### Decision: `relationship()` with default lazy loading + explicit `selectinload` at query time

**Decision**: Define the bidirectional `relationship()` with `lazy="select"` (default) on
both sides, and use `.options(selectinload(...))` at the call site when the related
collection is needed.

**Rationale**: Matches the existing query construction pattern in `app/api/auctions.py`.
Keeps loading strategies explicit and testable. `lazy="joined"` is problematic in async
context; `lazy="selectin"` risks loading unnecessarily when the relationship is not needed.

**Cascade**: `cascade="save-update"` only (no `delete-orphan`). The spec requires
AuctionEvent data to be retained indefinitely; deleting an AuctionEvent must never
cascade-delete its Auction children.

---

## "Cancelled" Flag vs. Deletion

### Decision: `is_cancelled: bool` stored on `AuctionEvent`; no deletion of event records

**Decision**: When an AuctionEvent disappears from the EEX calendar, set
`AuctionEvent.is_cancelled = True`. The record is never deleted. The associated `Auction`
records (upcoming) remain as-is.

**Rationale**: FR-010 / edge case spec is explicit: "Cancelled events are retained in the
database and marked as Cancelled; they remain visible in the dashboard with a clear
'Cancelled' label."

**Impact on existing sync logic**: `_remove_vanished_calendar_entries()` in `sync.py`
currently deletes upcoming `Auction` records that vanish from the calendar. This behavior
conflicts with the new requirement. The method must be refactored:
- Instead of deleting vanished upcoming `Auction` records, mark their parent `AuctionEvent`
  as `is_cancelled = True`.
- Individual `Auction` records linked to a cancelled event are retained.

---

## Sync Integration Point

### Decision: Integrate AuctionEvent sync into `run_daily()` and `run_manual()`; skip for backfill

**Decision**: AuctionEvent records are sourced only from the EEX live calendar (forward-
looking). The backfill path (Excel/ZIP archives) does not produce AuctionEvent records
because historical event metadata is not available from those sources.

**Rationale**: The calendar page only shows upcoming events; historical events are not
listed there. The backfill ZIP archives contain auction result rows (per region/technology)
with no event-grouping metadata.

For historical auction data already in the database (`status="past"`), the FK
`auction_event_id` will remain NULL until/unless a historical calendar source is identified.
This is acceptable per the spec.

**Alternatives considered**:
- Synthesize AuctionEvent stubs for historical dates by grouping existing `Auction` records
  by `auction_date` — possible but speculative; out of scope for this feature.

---

## Parser Strategy

### Decision: Add `scrape_auction_events()` as a new function in `parser.py`

**Decision**: Add a dedicated `scrape_auction_events()` function alongside the existing
`scrape_auction_calendar()`. Both fetch the same EEX page; `scrape_auction_events()`
returns event-shaped dicts (one per unique `event_date`), while `scrape_auction_calendar()`
continues to return auction-shaped dicts (one per upcoming calendar row, for backward
compatibility).

**Rationale**: Avoids breaking the existing `scrape_auction_calendar()` contract. The
two functions can share a helper for the HTTP fetch to avoid a double network round-trip.

---

## API Exposure

### Decision: New endpoint `GET /api/v1/auction-events`

**Decision**: Add a new FastAPI router `app/api/auction_events.py` with a single endpoint
`GET /api/v1/auction-events`. This returns a list of AuctionEvents (with computed status
and associated auctions). A query parameter `include_cancelled=false` controls whether
cancelled events are shown.

**Rationale**: The spec requires users to view events in the dashboard. The existing
upcoming auctions endpoint serves a different purpose (per-auction calendar view, not
event-grouped view). A dedicated endpoint keeps concerns separate and makes the new
feature independently testable.
