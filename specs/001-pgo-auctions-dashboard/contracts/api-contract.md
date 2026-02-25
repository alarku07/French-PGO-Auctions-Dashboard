# API Contract: French PGO Auctions Dashboard

**Feature**: 001-pgo-auctions-dashboard
**Date**: 2026-02-23
**Base URL**: `/api/v1`

All responses are JSON. All timestamps are ISO 8601 with timezone (UTC). Prices are in EUR. Volumes are in MWh.

---

## Endpoints

### 1. GET /api/v1/auctions

Returns past auction results with pagination and filtering.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string (YYYY-MM-DD) | No | First day of previous calendar month | Start of date range |
| `end_date` | string (YYYY-MM-DD) | No | Last day of previous calendar month | End of date range |
| `region` | string | No | (all) | Filter by region name |
| `technology` | string | No | (all) | Filter by technology type |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `page_size` | integer | No | 50 | Results per page (max 200) |
| `sort_by` | string | No | `auction_date` | Sort field: `auction_date`, `region`, `volume_allocated_mwh`, `weighted_avg_price_eur` |
| `sort_order` | string | No | `desc` | `asc` or `desc` |

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": 1,
      "auction_date": "2025-11-18",
      "region": "Auvergne-Rhone-Alpes",
      "production_period": "2025-08",
      "technology": null,
      "volume_offered_mwh": 243944.00,
      "volume_allocated_mwh": 243944.00,
      "num_bids": null,
      "num_winning_bids": null,
      "weighted_avg_price_eur": 0.3400,
      "status": "past"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 120,
    "total_pages": 3
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid date format, out-of-range page_size, unknown sort field
- `500 Internal Server Error`: Database connection failure

---

### 2. GET /api/v1/auctions/upcoming

Returns upcoming scheduled auctions (Auction records where `status = 'upcoming'`).

**Query Parameters**: None.

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": 42,
      "auction_date": "2026-03-18",
      "region": "Auvergne-Rhone-Alpes",
      "production_period": "2025-12",
      "order_book_open": "2026-03-11T10:00:00Z",
      "order_book_close": "2026-03-18T10:00:00Z",
      "order_matching": "2026-03-18T12:00:00Z"
    }
  ],
  "count": 3
}
```

When no upcoming auctions exist, returns `{"data": [], "count": 0}`.

Note: This endpoint queries the same `Auction` table as `GET /api/v1/auctions`, filtered to `status = 'upcoming'`. Calendar fields (`order_book_open`, `order_book_close`, `order_matching`) are only populated for upcoming records.

---

### 3. GET /api/v1/stats

Returns aggregate statistics for the dashboard overview.

**Query Parameters**: None.

**Response** (200 OK):

```json
{
  "total_auctions_held": 84,
  "total_volume_awarded_mwh": 12500000.00,
  "overall_weighted_avg_price_eur": 0.42,
  "last_updated": "2026-02-23T06:00:15Z"
}
```

- `last_updated` is the `completed_at` timestamp of the most recent successful sync.
- If no sync has ever run, `last_updated` is `null`.

---

### 4. GET /api/v1/charts/prices

Returns price time-series data for the price chart (FR-008).

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string (YYYY-MM-DD) | No | 5 years ago | Start of date range |
| `end_date` | string (YYYY-MM-DD) | No | today | End of date range |
| `region` | string | No | (all) | Filter by region name |
| `technology` | string | No | (all) | Filter by technology type (e.g., Wind, Hydro, Solar, Thermal) |

**Response** (200 OK):

```json
{
  "data": [
    {
      "auction_date": "2021-01-19",
      "region": "Auvergne-Rhone-Alpes",
      "weighted_avg_price_eur": 0.28,
      "volume_allocated_mwh": 180000.00
    }
  ],
  "filters": {
    "start_date": "2021-02-23",
    "end_date": "2026-02-23",
    "region": null,
    "technology": null
  }
}
```

---

### 5. GET /api/v1/charts/volumes

Returns volume time-series data for the volume chart (FR-009).

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string (YYYY-MM-DD) | No | 5 years ago | Start of date range |
| `end_date` | string (YYYY-MM-DD) | No | today | End of date range |
| `region` | string | No | (all) | Filter by region name |
| `technology` | string | No | (all) | Filter by technology type (e.g., Wind, Hydro, Solar, Thermal) |
| `aggregation` | string | No | `per_auction` | `per_auction`, `monthly`, `yearly` |

**Response** (200 OK):

```json
{
  "data": [
    {
      "period": "2025-11-18",
      "region": "Auvergne-Rhone-Alpes",
      "volume_offered_mwh": 243944.00,
      "volume_allocated_mwh": 243944.00
    }
  ],
  "filters": {
    "start_date": "2021-02-23",
    "end_date": "2026-02-23",
    "region": null,
    "technology": null,
    "aggregation": "per_auction"
  }
}
```

When `aggregation` is `monthly`, `period` format changes to `"2025-11"`.
When `aggregation` is `yearly`, `period` format changes to `"2025"`.

---

### 6. GET /api/v1/regions

Returns the list of regions available in the dataset.

**Query Parameters**: None.

**Response** (200 OK):

```json
{
  "data": [
    "Auvergne-Rhone-Alpes",
    "Bourgogne-Franche-Comte",
    "Bretagne",
    "Centre-Val de Loire",
    "Grand Est",
    "Hauts-de-France",
    "Ile-de-France",
    "Normandie",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Pays de la Loire",
    "Provence-Alpes-Cote d'Azur"
  ]
}
```

---

### 7. GET /api/v1/technologies

Returns the list of technology types available in the dataset.

**Query Parameters**: None.

**Response** (200 OK):

```json
{
  "data": [
    "Hydro",
    "Solar",
    "Thermal",
    "Wind"
  ]
}
```

Values are queried as `SELECT DISTINCT technology FROM auction WHERE technology IS NOT NULL ORDER BY technology`. The list reflects only technologies present in actual auction data.

---

## Common Response Patterns

### Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format for start_date. Expected YYYY-MM-DD.",
    "details": null
  }
}
```

### HTTP Status Codes Used

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Validation error (bad query params) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Security Headers (FR-019)

Every response includes:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

---

## CORS

CORS is configured to allow the frontend origin during development (`http://localhost:5173`) and the production domain. No credentials are needed (read-only, no auth).

---

## Rate Limiting

Not required for initial release. The dashboard is read-only and serves public data. Can be added at the reverse proxy level if needed.
