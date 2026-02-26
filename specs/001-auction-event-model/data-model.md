# Data Model: AuctionEvent

**Branch**: `001-auction-event-model` | **Phase**: Phase 1

---

## Entities

### AuctionEvent *(new table)*

Represents one auction session listed on the EEX French Auctions Calendar.
Uniquely identified by its calendar date.

| Field | Type | Nullable | Constraints | Notes |
|---|---|---|---|---|
| `id` | `Integer` | NO | PK, autoincrement | Surrogate key |
| `event_date` | `Date` | NO | UNIQUE | Calendar date of the auction session |
| `is_cancelled` | `Boolean` | NO | default=`false` | Set when event disappears from EEX calendar |
| `created_at` | `DateTime(tz)` | NO | default=`now()` | Record creation timestamp |
| `updated_at` | `DateTime(tz)` | NO | default=`now()`, onupdate | Last modification timestamp |

**Computed field** (not stored):

| Property | Formula | Values |
|---|---|---|
| `status` | `"upcoming"` if `event_date >= today`, else `"completed"` | `"upcoming"` / `"completed"` |

**Validation rules**:
- No two `AuctionEvent` rows may share the same `event_date`.
- `is_cancelled` may only transition `false → true`; reverting a cancellation is not
  supported in this version (out of scope).

**State transitions**:

```
event_date >= today  →  status = "upcoming"   (computed)
event_date < today   →  status = "completed"  (computed)
is_cancelled = false →  normal display
is_cancelled = true  →  shown with "Cancelled" label
```

---

### Auction *(existing table — modified)*

Two new columns added to link each `Auction` to its parent `AuctionEvent`.

| Field | Type | Nullable | Constraints | Notes |
|---|---|---|---|---|
| `auction_event_id` | `Integer` | YES | FK → `auction_event.id` | NULL for historical records pre-feature |

All other existing columns remain unchanged.

**Relationship**:
- `Auction.auction_event_id` → `AuctionEvent.id` (many-to-one)
- `AuctionEvent.auctions` (back-reference list, one-to-many)

---

## Entity-Relationship Diagram

```
auction_event                     auction
─────────────────────             ────────────────────────────────
id            PK                  id                PK
event_date    UNIQUE DATE    ←─── auction_event_id  FK (nullable)
is_cancelled  BOOLEAN             auction_date      DATE
created_at    TIMESTAMPTZ         region            VARCHAR
updated_at    TIMESTAMPTZ         production_period VARCHAR
                                  technology        VARCHAR
                                  status            VARCHAR
                                  ...               (existing cols)
```

Relationship cardinality: one `AuctionEvent` → zero or many `Auction` records.

---

## Alembic Migration

**Migration file**: `src/backend/alembic/versions/002_add_auction_event.py`

### Upgrade steps

1. Create `auction_event` table with all columns, PK, UNIQUE constraint, and indexes.
2. Add nullable `auction_event_id` column to `auction` table.
3. Add FK constraint `fk_auction_event` on `auction.auction_event_id → auction_event.id`.
4. Add index `idx_auction_event_id` on `auction.auction_event_id`.

### Downgrade steps

1. Drop FK constraint.
2. Drop index `idx_auction_event_id`.
3. Drop column `auction_event_id` from `auction`.
4. Drop table `auction_event`.

**Safety note**: The `auction_event_id` column is nullable so existing rows are unaffected.
No data migration is required; the FK is populated by the next sync run.

---

## Indexes

| Table | Index Name | Columns | Purpose |
|---|---|---|---|
| `auction_event` | `uq_auction_event_date` | `event_date` (UNIQUE) | Deduplication key |
| `auction_event` | `idx_auction_event_cancelled` | `is_cancelled` | Filter cancelled events |
| `auction` | `idx_auction_event_id` | `auction_event_id` | JOIN / selectinload |

---

## AuctionEvent Upsert Key

An `AuctionEvent` is uniquely identified by `event_date`. The upsert logic in the sync
service uses this field to decide create-or-update:

- **Create**: No existing `AuctionEvent` with this `event_date` → insert.
- **Update**: Existing record found → update `updated_at` only (no other mutable fields
  in V1; `is_cancelled` is managed separately via the cancelled-detection logic).
- **Cancel**: Existing record whose `event_date` no longer appears in the EEX calendar
  after a sync → set `is_cancelled = True`.
