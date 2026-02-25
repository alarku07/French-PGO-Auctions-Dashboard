# Research: French PGO Auctions Dashboard

**Feature**: 001-pgo-auctions-dashboard
**Date**: 2026-02-23

## 1. EEX Data Source Structure

### Decision
Fetch auction data from `https://www.eex.com/en/markets/energy-certificates/french-auctions-power` using direct HTTP downloads of Excel/ZIP files and HTML parsing for the latest results and calendar.

### Rationale
EEX does not expose a public API. Data is available as:
- **Latest auction results**: displayed directly on the webpage in HTML tables
- **Individual monthly Excel files**: e.g., `20260218_November_2025_9_GLOBAL_Results_detailedresults.xlsx`
- **Historical ZIP archives**: containing monthly Excel files bundled by year range

### Data Available on EEX

**Download URLs** (base: `https://www.eex.com`):

| Resource | Path | Size |
|----------|------|------|
| GO 2026 Global Results | `/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/20260220_GO_2026_GLOBAL_Results.zip` | ~228 KB |
| GO 2024-2025 Global Results | `/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/20251119_GO_2024_2025_GLOBAL_Results.zip` | ~3 MB |
| GO 2019-2023 Global Results | `/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/GO_2019-2023_Global_Results.zip` | varies |
| Calendar PDF 2026 | `/fileadmin/EEX/Downloads/Registry_Services/Guarantees_of_Origin_Documentation/2025_12_08_-_EEX_Registry_services_-_Customer_Information_-_French_GO_Auctions_Calendar_2026.pdf` | — |

**File naming convention**: `YYYYMMDD_MonthName_Year_N_GLOBAL_Results_detailedresults.xlsx`
- `YYYYMMDD` = publication date
- `MonthName_Year` = production month (the month the GOs relate to)
- `N` = auction sequence number within the year

**Legacy archive**: A historical Powernext archive may also be available at `https://gasandregistry.eex.com/Registry/GO/Historical_Data/GO_Historical_Data.zip` — to be checked during backfill implementation.

**Complementary data source (out of scope)**: Agence ORE publishes installation-level production data at `https://opendata.agenceore.fr/explore/dataset/suivi-encheres-go/` with a public API. This covers production volumes by region/technology but not clearing prices. Could be useful for future enrichment.

**EEX Market Data API**: A commercial REST API exists at `https://api1.datasource.eex-group.com/` but requires a paid subscription. Not viable for this project.

### Alternatives Considered
- **Web scraping only**: Fragile, depends on HTML structure. Rejected as sole approach but used for latest results and calendar which are only on the page.
- **Manual data entry**: Does not scale. Rejected.
- **EEX commercial API**: Exists but requires paid subscription. Not viable.

---

## 2. Auction Data Fields

### Decision
Model auction records with the following fields, derived from the EEX result tables and Excel files.

### Fields from EEX Results

**Summary table (on webpage, by Region):**

| Column | Type | Notes |
|--------|------|-------|
| Region | string | One of 12 French administrative regions |
| Volume Offered (MWh) | decimal | Total GOs offered for auction |
| Volume Allocated (MWh) | decimal | Total GOs awarded to buyers |
| Weighted Average Price (EUR/MWh) | decimal | Pay-as-bid weighted average |

**Summary table (on webpage, by Technology):**

| Column | Type | Notes |
|--------|------|-------|
| Technology | string | Wind, Hydro, Solar, Thermal |
| Volume Offered (MWh) | decimal | |
| Volume Allocated (MWh) | decimal | |
| Weighted Average Price (EUR/MWh) | decimal | |

**Detailed results Excel files** contain per-auction-event breakdowns including:
- Auction date
- Production period (month/year)
- Region
- Technology
- Volume offered / allocated
- Number of bids / winning bids
- Weighted average price

### Rationale
These fields align directly with spec requirements FR-001, FR-004, FR-008, FR-009, FR-010. The composite key (auction_date + region + production_period) matches the spec's deduplication requirement.

### Alternatives Considered
- **Store only summary data**: Would lose technology breakdown. Rejected — technology filter adds analytical value.
- **Store raw Excel blobs**: Would require re-parsing. Rejected — structured DB is faster and queryable.

---

## 3. French Regions (12 Administrative Regions)

### Decision
Use the 12 metropolitan French regions as published by EEX:

1. Auvergne-Rhone-Alpes
2. Bourgogne-Franche-Comte
3. Bretagne
4. Centre-Val de Loire
5. Grand Est
6. Hauts-de-France
7. Ile-de-France
8. Normandie
9. Nouvelle-Aquitaine
10. Occitanie
11. Pays de la Loire
12. Provence-Alpes-Cote d'Azur

### Rationale
These are the exact regions used in EEX auction results. Region names will be stored as-is from the source data to avoid mapping errors.

### Alternatives Considered
- **Use region codes (ISO 3166-2:FR)**: More compact but less readable; EEX uses full names. Rejected.
- **Allow dynamic region discovery**: Could lead to unexpected data. We enumerate known regions but gracefully accept unknown ones logged as warnings.

---

## 4. Technology Types

### Decision
Four technology categories for Power GOs as published by EEX:
1. Wind (onshore)
2. Hydro
3. Solar
4. Thermal

### Rationale
These are the exact categories used in the EEX auction breakdown tables. Marine energies are mentioned in some documentation but do not appear in current auction result data.

### Alternatives Considered
- **Include Marine as 5th type**: Not present in current data. Will be added dynamically if EEX starts publishing it.

---

## 5. Backend Framework Selection

### Decision
**FastAPI** with async SQLAlchemy and uvicorn.

### Rationale
- Constitution mandates async-first Python libraries
- FastAPI is the leading async Python web framework with automatic OpenAPI docs
- SQLAlchemy 2.0 async engine integrates well with FastAPI
- Uvicorn provides production-ready ASGI serving
- Built-in Pydantic validation for request/response schemas

### Alternatives Considered
- **Django + DRF**: More batteries-included but synchronous by default. Django async ORM is less mature than SQLAlchemy async. Rejected per async-first principle.
- **Flask**: Synchronous by default. Would need Quart for async. Smaller ecosystem for async patterns. Rejected.
- **Litestar**: Newer, smaller community. Rejected for stability and ecosystem maturity.

---

## 6. Frontend Charting Library

### Decision
**Apache ECharts** via `vue-echarts` wrapper.

### Rationale
- Rich interactive features (tooltips, zoom, pan, responsive resize) out of the box
- Excellent performance with large datasets (thousands of data points)
- Built-in responsive design
- Wide adoption and active maintenance
- Supports line charts, bar charts, scatter plots — all needed for price and volume visualisation
- Good Vue.js integration via `vue-echarts`

### Alternatives Considered
- **Chart.js (vue-chartjs)**: Simpler but less powerful for interactive exploration. Limited zoom/pan. Rejected for insufficient interactivity for analyst use case (US-2).
- **D3.js**: Maximum flexibility but low-level; requires building every chart feature manually. Overkill for this project. Rejected.
- **Plotly**: Good interactivity but heavier bundle size and more opinionated. Rejected for bundle weight.

---

## 7. Sync Strategy

### Decision
Two-phase sync approach:
1. **Initial backfill**: Download all ZIP archives, extract Excel files, parse and insert all historical records. Backfill is idempotent — safe to re-run; duplicates are skipped via the composite key. Downloaded ZIPs are cached in a persistent directory (`data/downloads/`) to avoid redundant downloads on re-runs.
2. **Daily incremental sync**: Scrape the latest results from the EEX webpage HTML and insert new records. Also update the auction calendar (see Calendar Sync below).

Sync is triggered by:
- **Automatic**: APScheduler running a daily job (configurable time, default 06:00 UTC). **Important**: uvicorn must run with exactly 1 worker when `SYNC_ENABLED=true` to prevent duplicate sync executions.
- **Manual**: CLI command (`python -m app.services.sync --manual`)

### Calendar Sync Strategy

The EEX auction calendar is available in two forms:
1. **HTML table on the main auctions page** — contains the current year's schedule with columns: Auctioning Month, Production Month, Order Book Opening, Order Book Closure, Order Matching.
2. **Annual PDF document** — published once per year with the same data.

**Decision**: Parse the calendar from the **HTML table** on the main EEX auctions page during each daily sync. This avoids PDF parsing complexity and ensures the calendar stays current if EEX makes mid-year adjustments.

**Approach**:
- During daily sync, scrape the calendar table from the HTML page alongside the latest results.
- For each calendar row, create or update an Auction record with `status = 'upcoming'`, populating `auction_date`, `production_period`, `order_book_open`, `order_book_close`, and `order_matching`.
- If a previously upcoming auction date has passed and results are found, transition the record to `status = 'past'` and fill in result fields.
- If a scheduled auction disappears from the calendar entirely, remove the corresponding upcoming record.
- If the HTML calendar structure changes, the parser logs a descriptive error and skips the calendar update without affecting result data.

**Fallback**: If the HTML calendar proves unreliable or is removed, the PDF can be parsed using `pdfplumber` as a fallback. This is not implemented in v1 but is noted as a contingency.

### Rationale
- ZIP archives contain the complete history (2019–present) and are downloaded once
- Daily results appear on the webpage before being bundled into ZIP archives
- APScheduler is lightweight and runs in-process with FastAPI
- CLI trigger satisfies FR-018 while FR-020 prevents public HTTP exposure
- HTML calendar parsing is simpler and more maintainable than PDF parsing

### Alternatives Considered
- **Celery + Redis**: Heavyweight for a single daily job. Rejected.
- **OS-level cron**: Works but harder to manage across platforms and less visible to the application. Rejected in favour of in-process scheduler.
- **HTTP endpoint for manual trigger**: Violates FR-020 (no public sync trigger). Rejected.
- **Parse calendar from PDF**: Requires `pdfplumber` or `camelot`, adds complexity, and PDFs are published once per year so may be stale. Rejected for v1; noted as fallback.

---

## 8. EEX Visual Identity

### Decision
Adopt the EEX corporate colour palette and typography for the dashboard.

### Visual Identity Elements (observed from EEX page)

| Element | Value |
|---------|-------|
| Primary text colour | Dark navy/black (#1a1a2e or similar dark) |
| Background | White (#ffffff) with light grey sections (#f5f5f5) |
| Accent / brand | Green for renewable energy theme elements, links, and highlights |
| Navigation | Dark (black/very dark grey) header bar |
| Table headers | Dark background with white text, alternating row zebra striping |
| Typography | Clean sans-serif system font stack (similar to Arial/Helvetica) |
| Layout style | Clean corporate, vertical content sections, generous whitespace |
| Hero/banner | Wind turbine imagery emphasising renewable energy |

### Rationale
Spec requirement FR-006 mandates adopting the EEX visual identity. The palette is publicly observable. We will approximate it using CSS custom properties for easy adjustment.

### Alternatives Considered
- **Custom brand identity**: Out of scope per FR-006. Rejected.
- **Material Design / Tailwind defaults**: Would not match EEX styling. Rejected.

---

## 9. Database Migration Strategy

### Decision
**Alembic** for database schema migrations, integrated with SQLAlchemy models.

### Rationale
- Standard migration tool for SQLAlchemy projects
- Supports auto-generation of migrations from model changes
- Works with both PostgreSQL and SQLite (for POC)
- Version-controlled migration history

### Alternatives Considered
- **Raw SQL migrations**: Error-prone, no rollback tracking. Rejected.
- **Django migrations**: Would require Django ORM. Not applicable with FastAPI + SQLAlchemy.

---

## 10. Excel Parsing Strategy

### Decision
**openpyxl** for parsing `.xlsx` files from EEX ZIP archives.

### Rationale
- Pure Python, no system dependencies
- Reads `.xlsx` format which is what EEX provides
- Constitution requires async-friendly where possible; openpyxl is CPU-bound so it will run in a thread pool executor to avoid blocking the event loop
- Handles the expected column layouts from EEX detailed results files

### Parsing Approach
1. Extract ZIP to temp directory
2. For each `.xlsx` file:
   - Detect header row by scanning for known column names
   - Map columns dynamically (resilient to minor layout changes)
   - Parse each data row into an Auction record
   - Log warnings for unrecognised column layouts (edge case from spec)
3. Bulk-insert/upsert into database using the composite key for deduplication

### Alternatives Considered
- **pandas**: Heavier dependency for simple tabular reads. Rejected for minimalism.
- **xlrd**: Only reads `.xls` (old format), not `.xlsx`. Not applicable.

---

## 11. Security Headers

### Decision
Implement security headers via FastAPI middleware per FR-019:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### Rationale
Read-only public site with no user data. Strict CSP prevents XSS. X-Frame-Options prevents clickjacking. No PII collection per FR-021.

### Alternatives Considered
- **Reverse proxy headers only (nginx)**: Coupling to deployment. Rejected — headers should be set at application level for portability.

---

## 12. Structured Logging

### Decision
Use Python `structlog` for structured JSON logging per Constitution Principle V.

### Log Format
```json
{
  "timestamp": "2026-02-23T10:15:30.123Z",
  "request_id": "uuid",
  "path": "/api/auctions",
  "method": "GET",
  "status": 200,
  "duration_ms": 45
}
```

### Rationale
Constitution V mandates structured logging with specific fields. `structlog` produces JSON logs suitable for aggregation tools while remaining readable in development.

### Alternatives Considered
- **Standard library logging + JSON formatter**: Works but less ergonomic than structlog. Acceptable fallback.
- **loguru**: Popular but less structured-output focused. Rejected for constitution compliance.
