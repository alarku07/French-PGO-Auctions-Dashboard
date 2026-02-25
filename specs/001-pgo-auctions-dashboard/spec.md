# Feature Specification: French PGO Auctions Dashboard

**Feature Branch**: `001-pgo-auctions-dashboard`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "Build a simple website to visualize French Power Guarantees of Origin auction results from EEX, with a local database, interactive graphs, and a periodic sync script."

## Clarifications

### Session 2026-02-23

- Q: Is the dashboard deployed on localhost, a private network, or the public internet? → A: Public internet — no authentication barrier. Local development comes first; public deployment is the final step.
- Q: What combination of fields uniquely identifies one Auction record for deduplication? → A: Composite key of auction date + region + production period + technology.
- Q: How many past auction records should the dashboard table show by default? → A: Last month's results only by default; full history accessible via the interactive charts and by adjusting the table filter.
- Q: Should the volume chart show per-auction data points or aggregated totals over time? → A: Both — per-auction view by default, with a toggle to switch to monthly/yearly aggregated view.
- Q: Should the sync process implement download delays or throttling when fetching EEX data? → A: No delay needed — there are few zip archives and they are downloaded only once during the initial full backfill; the daily incremental sync is a single lightweight request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Auction Dashboard Overview (Priority: P1)

An energy industry professional opens the dashboard to get an at-a-glance view of the
state of French Power Guarantee of Origin (PGO) auctions. They see a summary of recent
auction results, a list of upcoming auctions, and key statistics about the market — all
in one place, without needing to log in.

**Why this priority**: This is the core value of the product. All other capabilities
build on top of this foundational view. Without it, the dashboard has no value.

**Independent Test**: A user with no prior knowledge of the system can open the dashboard
URL and immediately see: at least one past auction result, at least one upcoming auction
date, the date the local data was last updated, and a summary statistic (e.g., total
volume auctioned). Testable with a pre-seeded test database, independently of the sync
logic.

**Acceptance Scenarios**:

1. **Given** the dashboard is open, **When** a user views it, **Then** they see a clearly
   labelled section listing past auctions for the previous calendar month, showing for
   each entry: auction date, region, volume offered (MWh), volume awarded (MWh), and
   average clearing price per MWh. A date-range filter allows viewing results from
   earlier periods.
2. **Given** the dashboard is open, **When** a user views it, **Then** they see a clearly
   labelled section showing upcoming scheduled auctions with at minimum: auction date and
   region.
3. **Given** the dashboard is open, **When** a user views it, **Then** they see a
   "Last updated" timestamp showing when the local database was last synced from the EEX
   source.
4. **Given** the dashboard is open, **When** a user views it, **Then** they see aggregate
   statistics: total number of auctions held, total volume ever awarded (MWh), and overall
   weighted average clearing price per MWh.
5. **Given** no upcoming auctions are currently scheduled, **When** a user views the
   upcoming section, **Then** they see a clear message indicating no auctions are
   currently scheduled.

---

### User Story 2 — Interactive Price and Volume Trend Exploration (Priority: P2)

An energy market analyst uses the dashboard to explore multi-year trends in PGO auction
clearing prices and volumes. They filter by region and time period to identify patterns
and decide whether to participate in an upcoming auction.

**Why this priority**: Understanding trends is the primary analytical use case. It turns
raw auction data into actionable market intelligence and is the reason energy professionals
would return to the dashboard regularly.

**Independent Test**: A user can open the interactive charts section, observe a line chart
showing clearing price per MWh over at least two years, switch the region filter, and see
the chart update within 2 seconds. Testable independently of the sync logic using a
pre-seeded database.

**Acceptance Scenarios**:

1. **Given** multiple years of auction data are available, **When** a user views the price
   chart, **Then** they see clearing price per MWh plotted over time with dates on the
   x-axis and price on the y-axis.
2. **Given** multiple years of auction data are available, **When** a user views the
   volume chart, **Then** they see total volume awarded (MWh) per individual auction
   plotted as discrete data points by default. A toggle control allows switching to a
   monthly or yearly aggregated view of the same data.
3. **Given** a user selects a specific region from a filter control, **When** the
   selection is applied, **Then** all charts and statistics update to reflect only data
   from that region.
4. **Given** a user hovers over a data point on any chart, **When** the hover is active,
   **Then** a tooltip displays the exact values for that point (date, price or volume,
   and region).
5. **Given** a user selects a custom time range, **When** the range is applied, **Then**
   charts update to display only data within that period.

---

### User Story 3 — Automatic Data Synchronisation (Priority: P3)

The system automatically and periodically checks the EEX French Auctions page for new
auction results and calendar updates, downloading and storing them in the local database
without any manual intervention.

**Why this priority**: Data freshness is essential for the dashboard to remain useful, but
the sync logic is a background concern. The P1 and P2 stories deliver value from a
pre-seeded database; P3 makes the system self-maintaining.

**Independent Test**: After triggering a manual sync run against a mocked EEX data source
containing a new auction result, that result appears in the local database and on the
dashboard, and the "Last updated" timestamp advances.

**Acceptance Scenarios**:

1. **Given** the sync process runs, **When** a new auction result is available on the EEX
   page, **Then** it is downloaded and added to the local database.
2. **Given** the sync process runs, **When** the EEX calendar has changed (new auctions
   added or dates updated), **Then** the local upcoming-auctions data is updated to match
   the current schedule.
3. **Given** a sync completes successfully, **When** the dashboard is viewed, **Then**
   the "Last updated" timestamp reflects the time of the most recent successful sync.
4. **Given** the EEX source is temporarily unavailable, **When** the sync runs, **Then**
   existing local data is preserved unchanged, the failure is logged internally, and the
   "Last updated" timestamp is not modified.
5. **Given** historical data zip archives are available from the EEX site, **When** an
   initial backfill sync is triggered, **Then** all available historical monthly Excel
   files are downloaded, parsed, and stored in the local database without overwriting
   previously validated records.

---

### Edge Cases

- What happens when the EEX website structure changes and auction data can no longer be
  parsed? The sync fails gracefully, existing data is preserved, and the failure is logged
  with a descriptive diagnostic message.
- What happens when an auction record contains missing fields (e.g., no clearing price
  published yet)? The record is stored with available fields; missing fields are displayed
  as "Not yet published" on the dashboard.
- What happens when the dashboard is accessed while a sync is in progress? The dashboard
  serves the current database state uninterrupted; the sync runs independently.
- What happens on first launch before any data has been downloaded? The dashboard
  displays a clear message guiding the operator to run the initial data sync.
- What happens if a historical Excel file contains unexpected column layouts? The parser
  logs a warning for that file and continues with the remaining files.

## Requirements *(mandatory)*

### Functional Requirements

**Dashboard display:**

- **FR-001**: The dashboard MUST display a list of past auctions showing, for each entry:
  auction date, region, volume offered (MWh), volume awarded (MWh), and average clearing
  price per MWh. By default, the table MUST show only the results from the previous
  calendar month. Users MUST be able to adjust the displayed period via a date-range
  filter to view older records. The full auction history remains accessible through the
  interactive charts (FR-008, FR-009).
- **FR-002**: The dashboard MUST display a list of upcoming scheduled auctions showing at
  minimum: auction date and region.
- **FR-003**: The dashboard MUST display a "Last updated" timestamp indicating when the
  local database was last successfully synchronised from the EEX source.
- **FR-004**: The dashboard MUST display aggregate statistics: total auctions held, total
  volume awarded (MWh), and overall weighted average clearing price per MWh.
- **FR-005**: The dashboard MUST be read-only. No user registration, login, or data-entry
  capability is present.
- **FR-006**: The dashboard MUST adopt the visual identity (colour palette, typography,
  and general layout style) of the EEX French Auctions Power web page.
- **FR-007**: Every page of the dashboard MUST render correctly on screen widths from
  320 px (smartphone) to 1920 px (desktop) without horizontal scrolling or broken layouts.

**Interactive charts:**

- **FR-008**: The dashboard MUST include an interactive chart showing average clearing
  price per MWh over time.
- **FR-009**: The dashboard MUST include an interactive chart showing total awarded volume
  (MWh) over time. The chart MUST default to a per-auction view where each auction event
  is a discrete data point. Users MUST be able to toggle to an aggregated view (monthly
  or yearly totals) without leaving the page.
- **FR-010**: Both charts MUST be filterable by region and by time range.
- **FR-011**: Both charts MUST display hover tooltips showing exact values for the data
  point under the cursor.
- **FR-012**: Charts MUST update dynamically when filters are changed, without requiring
  a full page reload.

**Data synchronisation:**

- **FR-013**: The system MUST include a periodic automated process that checks the EEX
  French Auctions Power page for new results and calendar updates on a daily schedule.
- **FR-014**: The sync process MUST download and parse the latest auction results from
  the EEX page.
- **FR-015**: The sync process MUST support downloading and parsing historical data from
  zip archives containing monthly Excel files, as provided by EEX for prior years. The
  full backfill (all available zip archives) is a one-time operation run once to seed the
  local database; no download throttling or delay is required given the small number of
  files involved.
- **FR-016**: The sync process MUST add newly discovered records to the local database
  without deleting or overwriting existing validated records. A record is considered a
  duplicate if another record already exists with the same auction date, region,
  production period, and technology; in that case the incoming record MUST be skipped
  or used only to fill in previously missing fields.
- **FR-017**: If the EEX source is unavailable during a sync, the process MUST log the
  failure internally, leave existing data untouched, and not update the "Last updated"
  timestamp.
- **FR-018**: The sync process MUST be runnable on-demand via a manual trigger, in
  addition to its automatic daily schedule.

**Public deployment security:**

- **FR-019**: The dashboard MUST serve standard web security headers on every response,
  including at minimum: `Content-Security-Policy`, `X-Frame-Options`, and
  `X-Content-Type-Options`, appropriate for a publicly accessible, read-only application.
- **FR-020**: The manual sync trigger MUST NOT be exposed as a public HTTP endpoint. It
  MUST be restricted to server-side invocation only (e.g., command-line execution or a
  locally scheduled task), so that external users cannot initiate data-fetching operations.
- **FR-021**: The dashboard MUST NOT collect, store, or transmit any personally
  identifiable information about its visitors. No cookies requiring user consent, no
  analytics tracking scripts, and no user-generated content are permitted.

### Key Entities *(include if feature involves data)*

- **Auction**: A single auction event. Key attributes: auction date, region, status
  (past / upcoming), technology (Wind, Hydro, Solar, Thermal), volume offered (MWh),
  volume awarded (MWh), number of bids, number of winning bids, clearing price per MWh,
  production period (the month/year the GOs relate to), and optional calendar fields
  (order book open/close, order matching timestamps) for upcoming auctions. **Unique
  identity**: the combination of auction date + region + production period + technology
  forms the composite natural key used for deduplication during sync.
- **Region**: A geographic or administrative zone in France for which Power GOs are
  auctioned (as defined by EEX publications, e.g., mainland France or specific energy
  zones).
- **Sync Log**: A record of each synchronisation run. Key attributes: run timestamp,
  outcome (success / failure), number of records added or updated, error message if
  applicable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An energy professional can open the dashboard and locate the most recent
  completed auction result within 10 seconds of the page loading, without navigating away
  from the main page.
- **SC-002**: An analyst can change the region filter on the price chart and see the
  updated chart within 2 seconds.
- **SC-003**: During normal operation, the "Last updated" timestamp always reflects a
  successful sync performed within the previous 24 hours — confirming daily sync
  reliability.
- **SC-004**: The full historical dataset available on EEX is accessible and visible on
  the charts; analysts can view price and volume trends spanning at least 5 years.
- **SC-005**: The dashboard is fully usable on both a standard desktop browser and a
  smartphone browser, with no broken layouts or inaccessible controls.
- **SC-006**: When the EEX source is temporarily unavailable, the dashboard continues to
  serve existing data with no visible error to end users; only the sync log reflects the
  failure.

## Assumptions

- EEX publishes auction results the day after each auction; a daily sync cadence is
  sufficient to keep the dashboard current. The number of historical zip archives is
  small enough that the one-time full backfill completes without throttling or delay.
- The volume of auctions is low enough (monthly events per region) that the full
  historical dataset fits comfortably in a local database without performance concerns.
- All historical zip/Excel files from EEX follow a consistent, parsable structure; minor
  format variations across years are handleable by the parser.
- The EEX website's colour palette and typography are publicly observable and may be
  referenced for styling the dashboard.
- The dashboard interface will use English-language labels (consistent with the EEX
  English site).
- The dashboard is deployed on the public internet with no authentication. Because it
  serves only publicly available auction data and collects no user data, the security
  surface is limited to web security headers and protection of the server-side sync
  trigger. Development is validated locally before any public deployment.
- "Region" in the auction data corresponds to geographic or administrative zones as
  published by EEX; the exact list of regions is determined at implementation time by
  inspecting the source data.

## Scope & Exclusions

**In scope:**

- Dashboard showing past auctions, upcoming auctions, aggregate statistics, and "Last
  updated" timestamp.
- Interactive price and volume charts filterable by region and time range.
- Local database storing all auction data.
- Automated daily sync process with manual trigger capability.
- Historical backfill from EEX zip/Excel archives.
- Responsive design (mobile to desktop).
- EEX-aligned visual identity.

**Out of scope:**

- User accounts, authentication, or authorisation.
- Ability to submit bids or interact with EEX trading systems.
- Push notifications or email alerts when new auctions are published.
- User-facing data export (e.g., CSV download from the dashboard).
- Integration with trading, portfolio, or ERP systems.
- Support for non-Power GO auctions (e.g., Biogas GOs available on EEX).
- Multi-language support beyond English.
