"""Unit tests for GET /api/v1/auction-events and /auction-events/years endpoints (US1).

Uses an in-memory SQLite database (see conftest.py). Verifies:
- Empty DB returns 200 with empty list
- AuctionEvents returned with computed status field
- Cancelled events excluded by default; included when requested
- Nested auctions appear in the response
- Invalid date params return 400
"""
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction
from app.models.auction_event import AuctionEvent


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _seed_event(
    session: AsyncSession,
    event_date: date,
    is_cancelled: bool = False,
    auctioning_month: str | None = None,
    production_month: str | None = None,
    order_book_open: datetime | None = None,
    cash_trading_limits_modification: datetime | None = None,
    order_book_close: datetime | None = None,
    order_matching: datetime | None = None,
) -> AuctionEvent:
    event = AuctionEvent(
        event_date=event_date,
        is_cancelled=is_cancelled,
        auctioning_month=auctioning_month,
        production_month=production_month,
        order_book_open=order_book_open,
        cash_trading_limits_modification=cash_trading_limits_modification,
        order_book_close=order_book_close,
        order_matching=order_matching,
    )
    session.add(event)
    await session.flush()
    return event


async def _seed_auction(
    session: AsyncSession,
    auction_date: date,
    region: str = "Bretagne",
    production_period: str = "2026-01",
    technology: str | None = None,
    status: str = "upcoming",
    auction_event_id: int | None = None,
) -> Auction:
    auction = Auction(
        auction_date=auction_date,
        region=region,
        production_period=production_period,
        technology=technology,
        status=status,
        auction_event_id=auction_event_id,
    )
    session.add(auction)
    await session.flush()
    return auction


# ─── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auction_events_empty_db_returns_200(client: AsyncClient) -> None:
    """Empty DB returns 200 with empty list."""
    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_upcoming_event_has_status_upcoming(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An AuctionEvent with a future date has computed status 'upcoming'."""
    future_date = date.today() + timedelta(days=10)
    event = await _seed_event(db_session, future_date)
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["id"] == event.id
    assert data["data"][0]["event_date"] == future_date.isoformat()
    assert data["data"][0]["status"] == "upcoming"
    assert data["data"][0]["is_cancelled"] is False


@pytest.mark.asyncio
async def test_past_event_has_status_completed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An AuctionEvent with a past date has computed status 'completed'."""
    past_date = date.today() - timedelta(days=30)
    event = await _seed_event(db_session, past_date)
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_cancelled_event_excluded_by_default(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Cancelled events are hidden unless include_cancelled=true."""
    future_date = date.today() + timedelta(days=5)
    await _seed_event(db_session, future_date, is_cancelled=True)
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["data"] == []


@pytest.mark.asyncio
async def test_cancelled_event_included_when_requested(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Cancelled events appear when include_cancelled=true."""
    future_date = date.today() + timedelta(days=5)
    event = await _seed_event(db_session, future_date, is_cancelled=True)
    await db_session.commit()

    response = await client.get(
        "/api/v1/auction-events", params={"include_cancelled": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["id"] == event.id
    assert data["data"][0]["is_cancelled"] is True


@pytest.mark.asyncio
async def test_auctions_nested_in_event(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Associated Auction records appear nested inside the event response."""
    event_date = date.today() + timedelta(days=15)
    event = await _seed_event(db_session, event_date)
    await _seed_auction(
        db_session,
        auction_date=event_date,
        region="Grand Est",
        production_period="2026-03",
        technology="Wind",
        status="upcoming",
        auction_event_id=event.id,
    )
    await _seed_auction(
        db_session,
        auction_date=event_date,
        region="Bretagne",
        production_period="2026-03",
        technology="Solar",
        status="upcoming",
        auction_event_id=event.id,
    )
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    auctions = data["data"][0]["auctions"]
    assert len(auctions) == 2
    regions = {a["region"] for a in auctions}
    assert regions == {"Grand Est", "Bretagne"}


@pytest.mark.asyncio
async def test_event_with_no_auctions_returns_empty_list(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """An AuctionEvent with no associated auctions returns auctions=[]."""
    event_date = date.today() + timedelta(days=20)
    event = await _seed_event(db_session, event_date)
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["auctions"] == []


@pytest.mark.asyncio
async def test_start_date_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """start_date filter excludes events before the given date."""
    past_date = date.today() - timedelta(days=60)
    future_date = date.today() + timedelta(days=30)
    await _seed_event(db_session, past_date)
    await _seed_event(db_session, future_date)
    await db_session.commit()

    today_str = date.today().isoformat()
    response = await client.get(
        "/api/v1/auction-events", params={"start_date": today_str}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["data"][0]["event_date"] == future_date.isoformat()


@pytest.mark.asyncio
async def test_invalid_start_date_returns_400(client: AsyncClient) -> None:
    """Invalid date format for start_date returns 400."""
    response = await client.get(
        "/api/v1/auction-events", params={"start_date": "not-a-date"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_events_sorted_descending_by_date(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Events are returned sorted by event_date descending."""
    dates = [
        date.today() + timedelta(days=d) for d in [5, 15, 2, 30]
    ]
    for d in dates:
        await _seed_event(db_session, d)
    await db_session.commit()

    response = await client.get("/api/v1/auction-events")
    assert response.status_code == 200
    returned_dates = [e["event_date"] for e in response.json()["data"]]
    assert returned_dates == sorted(returned_dates, reverse=True)


# ─── /auction-events/years ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_years_empty_db_returns_empty_list(client: AsyncClient) -> None:
    """Empty DB returns 200 with empty years list."""
    response = await client.get("/api/v1/auction-events/years")
    assert response.status_code == 200
    assert response.json() == {"data": []}


@pytest.mark.asyncio
async def test_years_returns_distinct_years_descending(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Returns distinct years from event_date, sorted descending."""
    await _seed_event(db_session, date(2024, 3, 15))
    await _seed_event(db_session, date(2025, 6, 10))
    await _seed_event(db_session, date(2025, 11, 20))  # same year as above
    await _seed_event(db_session, date(2026, 1, 8))
    await db_session.commit()

    response = await client.get("/api/v1/auction-events/years")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data == [2026, 2025, 2024]  # distinct, descending
