# Data Model: French PGO Auctions Dashboard

**Feature**: 001-pgo-auctions-dashboard
**Date**: 2026-02-23

## Entities

### 1. Auction

Represents a single auction event — both past results and upcoming scheduled auctions live in this table, distinguished by `status`. One row per (auction_date, region, production_period, technology) combination.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | BIGINT (PK) | AUTO INCREMENT | Surrogate primary key |
| `auction_date` | DATE | NOT NULL | Date the auction was/will be held |
| `region` | VARCHAR(100) | NOT NULL | French administrative region name |
| `production_period` | VARCHAR(20) | NOT NULL | Month/year the GOs relate to (e.g., "2025-11") |
| `technology` | VARCHAR(50) | NULLABLE | Wind, Hydro, Solar, Thermal (NULL for aggregate/upcoming rows) |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'upcoming' | 'past' or 'upcoming' |
| `volume_offered_mwh` | DECIMAL(12,2) | NULLABLE | Total GOs offered (MWh) — NULL for upcoming |
| `volume_allocated_mwh` | DECIMAL(12,2) | NULLABLE | Total GOs awarded (MWh) — NULL for upcoming |
| `num_bids` | INTEGER | NULLABLE | Number of bids received |
| `num_winning_bids` | INTEGER | NULLABLE | Number of winning bids |
| `weighted_avg_price_eur` | DECIMAL(10,4) | NULLABLE | Weighted average clearing price (EUR/MWh) |
| `reserve_price_eur` | DECIMAL(10,4) | NULLABLE | DGEC reserve/floor price (EUR/MWh), currently 0.15 |
| `order_book_open` | TIMESTAMPTZ | NULLABLE | When order book opens (calendar data, upcoming only) |
| `order_book_close` | TIMESTAMPTZ | NULLABLE | When order book closes (calendar data, upcoming only) |
| `order_matching` | TIMESTAMPTZ | NULLABLE | When order matching occurs (calendar data, upcoming only) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Composite unique constraint**: `UNIQUE(auction_date, region, production_period, technology)`

This is the natural key used for deduplication during sync (FR-016). When a duplicate is detected, the incoming record fills in previously NULL fields but does not overwrite existing non-NULL values.

**Indexes**:
- `idx_auction_date` on `auction_date` — for date-range queries (FR-001, FR-010)
- `idx_auction_region` on `region` — for region filter queries (FR-010)
- `idx_auction_status` on `status` — for upcoming vs past partitioning (FR-001, FR-002)
- `idx_auction_composite` on `(auction_date, region, production_period, technology)` — unique constraint index

**CHECK constraints** (database-level enforcement):
- `CHECK (status IN ('past', 'upcoming'))`
- `CHECK (technology IN ('Wind', 'Hydro', 'Solar', 'Thermal') OR technology IS NULL)`
- `CHECK (volume_offered_mwh >= 0 OR volume_offered_mwh IS NULL)`
- `CHECK (volume_allocated_mwh >= 0 OR volume_allocated_mwh IS NULL)`
- `CHECK (weighted_avg_price_eur >= 0 OR weighted_avg_price_eur IS NULL)`
- `CHECK (reserve_price_eur >= 0 OR reserve_price_eur IS NULL)`

**Validation Rules** (application-level):
- `auction_date` must be a valid date
- `region` must be a non-empty string (validated against known regions, with warnings for unknown ones)
- `production_period` must match format `YYYY-MM`
- `volume_allocated_mwh` <= `volume_offered_mwh` when both are present

**State Transitions**:
```
upcoming → past    (when auction completes and results are published)
```
An upcoming auction record transitions to 'past' when the sync process discovers result data for that auction date. The record is updated in place: `status` changes to 'past', result fields (volumes, price, bids) are filled in, and calendar fields (`order_book_open`, `order_book_close`, `order_matching`) are preserved for historical reference.

If an auction date passes with no results published, the upcoming record is kept as-is (not auto-deleted). If a scheduled auction disappears from the calendar, the sync removes it.

---

### 2. SyncLog

Records each synchronisation run for auditability and to support the "Last updated" display (FR-003).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | BIGINT (PK) | AUTO INCREMENT | Surrogate primary key |
| `run_timestamp` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When the sync started |
| `completed_at` | TIMESTAMPTZ | NULLABLE | When the sync finished |
| `outcome` | VARCHAR(20) | NOT NULL | 'success', 'failure', 'partial' |
| `sync_type` | VARCHAR(20) | NOT NULL | 'daily', 'backfill', 'manual' |
| `records_added` | INTEGER | NOT NULL, DEFAULT 0 | New records inserted |
| `records_updated` | INTEGER | NOT NULL, DEFAULT 0 | Existing records with fields filled in |
| `records_skipped` | INTEGER | NOT NULL, DEFAULT 0 | Duplicate records skipped |
| `error_message` | TEXT | NULLABLE | Diagnostic message on failure |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |

**Indexes**:
- `idx_sync_timestamp` on `run_timestamp DESC` — for "Last updated" query (most recent first)
- `idx_sync_outcome` on `outcome` — for filtering successful syncs

**No state transitions**: SyncLog records are append-only. They are never updated after completion (the `completed_at` and final counts are set once when the sync finishes).

---

## Entity Relationships

```
Auction (0..*)  ←  relates to region  →  (implicit, no Region table)
SyncLog (0..*)  ←  independent audit trail
```

**Design decisions**:
- Region is not a separate table. The 12 regions are well-known and stable; storing them as strings in the Auction table avoids an unnecessary join. If EEX adds regions, they appear naturally in the data. An application-level enum validates known regions and logs warnings for unknown ones.
- Upcoming auctions and past results share a single `Auction` table, distinguished by `status`. Calendar-only fields (`order_book_open`, `order_book_close`, `order_matching`) are nullable and only populated for upcoming entries. When an auction completes, the record transitions in place from 'upcoming' to 'past'.

---

## Aggregate Queries (for FR-004 Statistics)

The following aggregates are computed at query time, not materialised:

| Statistic | Query |
|-----------|-------|
| Total auctions held | `COUNT(DISTINCT auction_date) WHERE status = 'past'` |
| Total volume awarded (MWh) | `SUM(volume_allocated_mwh) WHERE status = 'past' AND technology IS NULL` |
| Overall weighted avg price | `SUM(weighted_avg_price_eur * volume_allocated_mwh) / SUM(volume_allocated_mwh) WHERE status = 'past' AND technology IS NULL` |
| Last updated timestamp | `MAX(completed_at) FROM sync_log WHERE outcome = 'success'` |

Note: Aggregate-level rows (technology IS NULL) represent per-region totals from the EEX summary tables. Technology-specific rows provide the breakdown.
