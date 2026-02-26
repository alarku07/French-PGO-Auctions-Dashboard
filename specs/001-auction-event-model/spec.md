# Feature Specification: AuctionEvent Model

**Feature Branch**: `001-auction-event-model`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Add AuctionEvent model to the application. AuctionEvent is a group of auctions happening in a single month and usually on the same day. AuctioningEvent can be fetched from https://www.eex.com/en/markets/energy-certificates/french-auctions-power under Caldendar. This must also be periodically updated in database during the data update script"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Auction Events in Dashboard (Priority: P1)

A dashboard user wants to browse French PGO auction events grouped by date and month, so they can quickly understand when auction activity is happening and what auctions belong to each event.

**Why this priority**: This is the primary user-facing value of the feature. Without the ability to view auction events, the underlying data has no purpose in the dashboard.

**Independent Test**: Can be fully tested by opening the dashboard and verifying that a list of auction events is displayed, each showing its date, the month it belongs to, and the auctions associated with it.

**Acceptance Scenarios**:

1. **Given** the application has stored auction events, **When** a user opens the dashboard, **Then** they see a list of auction events each with a date and the auctions grouped under it.
2. **Given** an auction event with multiple auctions, **When** the user views that event, **Then** all associated auctions are shown under the same event entry.
3. **Given** auction events for different months, **When** the user browses the list, **Then** events are organized chronologically.

---

### User Story 2 - Automatic Data Synchronization from EEX Calendar (Priority: P2)

The system automatically retrieves the latest auction event schedule from the EEX French Auctions Calendar and stores it in the application database, so that the dashboard always reflects the most up-to-date auction schedule without manual intervention.

**Why this priority**: Without up-to-date data, the dashboard loses its core value. Automation removes the risk of stale information and eliminates manual work.

**Independent Test**: Can be fully tested by triggering the data update process and verifying that auction events from the EEX calendar appear in the database, including any newly added or modified events.

**Acceptance Scenarios**:

1. **Given** the EEX calendar contains auction events not yet in the database, **When** the data update runs, **Then** those new events are added to the database.
2. **Given** an existing auction event whose date has changed on EEX, **When** the data update runs, **Then** the stored event is updated to reflect the new date.
3. **Given** the EEX calendar is temporarily unavailable, **When** the data update runs, **Then** the update fails gracefully without corrupting existing data and the failure is logged.
4. **Given** the data update has already imported an auction event, **When** the update runs again with no changes on EEX, **Then** no duplicate records are created.

---

### User Story 3 - Historical and Future Auction Event Visibility (Priority: P3)

A dashboard user wants to distinguish between past and upcoming auction events so they can analyze historical activity and plan for future auctions.

**Why this priority**: Useful for analysis but not critical for MVP; past and future context add analytical value once the base model is in place.

**Independent Test**: Can be fully tested by verifying that the dashboard correctly labels events as past or upcoming based on the current date.

**Acceptance Scenarios**:

1. **Given** auction events with dates before today, **When** a user views the dashboard, **Then** those events are visibly marked as past events.
2. **Given** auction events with dates after today, **When** a user views the dashboard, **Then** those events are visibly marked as upcoming events.
3. **Given** an auction event that was removed from the EEX calendar, **When** a user views the dashboard, **Then** that event is still displayed with a clear "Cancelled" label alongside active events.

---

### Edge Cases

- What happens when the EEX calendar is unavailable during a scheduled data update? (Existing data must not be modified; failure is logged.)
- What happens when an auction event on EEX has no associated individual auctions yet? (The event is stored without auctions; auctions are added on subsequent updates.)
- How does the system handle an auction event that is removed from the EEX calendar? (Event is retained in the database and marked as **Cancelled**; it remains visible in the dashboard with a clear "Cancelled" label.)
- What if two data updates run simultaneously? (Second update is skipped or queued to prevent data conflicts.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define an AuctionEvent as a named grouping of auctions occurring within a single month, typically on the same calendar day.
- **FR-002**: System MUST store each AuctionEvent with at minimum: event date, the month and year it belongs to, and its association to one or more individual auctions. The upcoming/completed status is derived at display time from the event date and does not require a separate stored field.
- **FR-003**: System MUST retrieve AuctionEvent data from the EEX French Auctions Power Calendar as the authoritative data source.
- **FR-004**: System MUST run the AuctionEvent data retrieval as part of the existing periodic data update process.
- **FR-005**: System MUST upsert AuctionEvents on each update cycle — creating new events and updating changed events without creating duplicates. An AuctionEvent is uniquely identified by its event date; no two AuctionEvents may share the same calendar date.
- **FR-006**: System MUST associate each AuctionEvent with the individual auctions that belong to it.
- **FR-007**: System MUST log the outcome (success, failure, number of events added/updated) of each AuctionEvent synchronization run.
- **FR-008**: System MUST preserve existing AuctionEvent data if the data source is unreachable during a scheduled update.
- **FR-009**: Users MUST be able to view AuctionEvents in the dashboard, showing each event's date and its associated auctions.
- **FR-010**: AuctionEvents that have been removed from the EEX calendar MUST remain visible in the dashboard with a clear "Cancelled" label, and MUST NOT be deleted from the system.

### Key Entities

- **AuctionEvent**: Represents a scheduled auction session in a given month. Key attributes: event date (specific calendar date, **primary unique identifier**), month/year (the month this event belongs to), list of associated auctions. Status (upcoming/completed) is **computed** based on whether the event date is on or after today (upcoming) or in the past (completed) — it is not a stored field. An AuctionEvent groups one or more individual Auctions occurring on the same day. No two AuctionEvents may share the same event date.
- **Auction**: An individual auction that belongs to an AuctionEvent. Already exists in the application; this feature establishes the relationship between Auction and AuctionEvent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All auction events listed on the EEX French Auctions Calendar are reflected in the dashboard within 24 hours of a scheduled data update.
- **SC-002**: The data update process completes without manual intervention for 100% of scheduled runs under normal network conditions.
- **SC-003**: Zero existing auction event records are lost or corrupted during any data update cycle.
- **SC-004**: Users can view any auction event and its associated auctions in under 3 seconds.
- **SC-005**: Duplicate auction events are never created — running the update multiple times with unchanged source data results in the same number of stored events.

## Clarifications

### Session 2026-02-25

- Q: What uniquely identifies an AuctionEvent for deduplication during upsert? → A: Event date alone — each unique calendar date identifies one AuctionEvent.
- Q: What triggers the AuctionEvent status transition from "upcoming" to "completed"? → A: Time-based — status is computed from the event date relative to today; no stored or EEX-sourced status field required.
- Q: How should cancelled (EEX-removed) auction events appear in the dashboard? → A: Shown in the main list with a visible "Cancelled" label, not hidden.

## Assumptions

- The EEX French Auctions Calendar publicly lists auction events with at minimum: a date and the individual auctions scheduled for that day.
- An "auction event" corresponds to a single day's auction session in a given month; one month may have multiple auction events on different days.
- The application already has an existing data update script that this feature will be integrated into.
- The application already has an Auction model; this feature adds the AuctionEvent grouping layer and links it to existing auctions.
- Data updates run on a daily schedule; if the source is unavailable, the next scheduled run will pick up the latest data.
- Historical auction events (past dates) are retained in the database indefinitely and displayed in the dashboard alongside upcoming events.
