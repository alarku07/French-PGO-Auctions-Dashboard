# API Contract: AuctionEvent Endpoints

**Branch**: `001-auction-event-model` | **Phase**: Phase 1

---

## New Endpoint

### `GET /api/v1/auction-events`

Returns a list of AuctionEvents, each showing its date, computed status, cancellation
state, and associated auctions.

#### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `include_cancelled` | `bool` | `false` | When `true`, includes events marked as cancelled |
| `start_date` | `string` (YYYY-MM-DD) | none | Filter events on or after this date |
| `end_date` | `string` (YYYY-MM-DD) | none | Filter events on or before this date |

#### Response: `200 OK`

```json
{
  "data": [
    {
      "id": 42,
      "event_date": "2026-03-18",
      "status": "upcoming",
      "is_cancelled": false,
      "auctions": [
        {
          "id": 101,
          "auction_date": "2026-03-18",
          "region": "Grand Est",
          "production_period": "2026-01",
          "technology": "Wind",
          "status": "upcoming"
        },
        {
          "id": 102,
          "auction_date": "2026-03-18",
          "region": "Bretagne",
          "production_period": "2026-01",
          "technology": "Solar",
          "status": "upcoming"
        }
      ]
    },
    {
      "id": 38,
      "event_date": "2026-01-14",
      "status": "completed",
      "is_cancelled": false,
      "auctions": [
        {
          "id": 88,
          "auction_date": "2026-01-14",
          "region": "Grand Est",
          "production_period": "2025-11",
          "technology": "Wind",
          "status": "past"
        }
      ]
    }
  ],
  "count": 2
}
```

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `data` | `array` | Array of AuctionEvent objects, sorted by `event_date` descending |
| `count` | `integer` | Total number of returned events |
| `data[].id` | `integer` | Surrogate key |
| `data[].event_date` | `string` (YYYY-MM-DD) | The auction session date |
| `data[].status` | `"upcoming"` \| `"completed"` | Computed from `event_date` vs today; never stored |
| `data[].is_cancelled` | `boolean` | `true` if the event was removed from the EEX calendar |
| `data[].auctions` | `array` | Associated Auction records (may be empty for future events) |
| `data[].auctions[].id` | `integer` | |
| `data[].auctions[].auction_date` | `string` (YYYY-MM-DD) | |
| `data[].auctions[].region` | `string` | |
| `data[].auctions[].production_period` | `string` (YYYY-MM) | |
| `data[].auctions[].technology` | `string` \| `null` | `null` for aggregate rows |
| `data[].auctions[].status` | `"past"` \| `"upcoming"` | Stored on Auction |

#### Error responses

| Status | Code | When |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Invalid `start_date` or `end_date` format |

---

## Unchanged Existing Endpoints

The following existing endpoints are **not changed** by this feature:

| Endpoint | Notes |
|---|---|
| `GET /api/v1/auctions` | Returns past auction results; unaffected |
| `GET /api/v1/auctions/upcoming` | Returns upcoming per-auction calendar rows; unaffected |
| `GET /api/v1/regions` | Unaffected |
| `GET /api/v1/technologies` | Unaffected |
| `GET /api/v1/stats` | Unaffected |

---

## Pydantic Schema Reference

**New schemas** (in `app/schemas/auction_event.py`):

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
    status: str           # computed, not from DB
    is_cancelled: bool
    auctions: list[AuctionSummary]

class AuctionEventListResponse(BaseModel):
    data: list[AuctionEventResponse]
    count: int
```
