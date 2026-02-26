"""Unit tests for AuctionEvent sync service methods (US2).

Tests the following methods on SyncService:
- _upsert_auction_event: create new / skip existing / update detail fields
- _bulk_upsert_auction_events: deduplication across a batch
- _link_auctions_to_events: FK set on Auction rows matching event date
- _mark_cancelled_events: flag vanished upcoming dates; leave past events alone
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction
from app.models.auction_event import AuctionEvent
from app.services.sync import SyncService


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _make_service() -> SyncService:
    return SyncService(
        database_url="sqlite+aiosqlite:///:memory:",
        eex_base_url="https://www.eex.com",
    )


def _make_event_dict(
    event_date: date,
    is_cancelled: bool = False,
    auctioning_month: str | None = None,
    production_month: str | None = None,
    order_book_open: datetime | None = None,
    cash_trading_limits_modification: datetime | None = None,
    order_book_close: datetime | None = None,
    order_matching: datetime | None = None,
) -> dict:
    return {
        "event_date": event_date,
        "is_cancelled": is_cancelled,
        "auctioning_month": auctioning_month,
        "production_month": production_month,
        "order_book_open": order_book_open,
        "cash_trading_limits_modification": cash_trading_limits_modification,
        "order_book_close": order_book_close,
        "order_matching": order_matching,
    }


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
    production_period: str = "2026-03",
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


# ─── _upsert_auction_event ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_creates_new_event(db_session: AsyncSession) -> None:
    """Upserting a date not yet in DB creates a new AuctionEvent."""
    service = _make_service()
    future = date.today() + timedelta(days=10)

    outcome = await service._upsert_auction_event(
        db_session, _make_event_dict(future)
    )
    await db_session.flush()

    assert outcome == "added"
    result = await db_session.execute(
        select(AuctionEvent).where(AuctionEvent.event_date == future)
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.is_cancelled is False


@pytest.mark.asyncio
async def test_upsert_skips_existing_event(db_session: AsyncSession) -> None:
    """Upserting an already-stored date is a no-op (skipped)."""
    service = _make_service()
    future = date.today() + timedelta(days=15)
    await _seed_event(db_session, future)

    outcome = await service._upsert_auction_event(
        db_session, _make_event_dict(future)
    )

    assert outcome == "skipped"
    result = await db_session.execute(select(AuctionEvent))
    events = result.scalars().all()
    assert len(events) == 1  # no duplicate


@pytest.mark.asyncio
async def test_upsert_updates_detail_fields_on_existing_event(
    db_session: AsyncSession,
) -> None:
    """Upserting over an existing event refreshes the detail fields."""
    service = _make_service()
    future = date.today() + timedelta(days=20)
    closure_dt = datetime(future.year, future.month, future.day, 16, 0)
    await _seed_event(db_session, future)

    event_dict = _make_event_dict(
        future,
        auctioning_month="March 2026",
        production_month="March 2026",
        order_book_close=closure_dt,
    )
    outcome = await service._upsert_auction_event(db_session, event_dict)
    await db_session.flush()

    assert outcome == "skipped"
    result = await db_session.execute(
        select(AuctionEvent).where(AuctionEvent.event_date == future)
    )
    event = result.scalar_one()
    assert event.auctioning_month == "March 2026"
    assert event.order_book_close == closure_dt


# ─── _bulk_upsert_auction_events ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_upsert_inserts_all_new(db_session: AsyncSession) -> None:
    """All new dates produce added=N, skipped=0."""
    service = _make_service()
    dicts = [_make_event_dict(date.today() + timedelta(days=d)) for d in [5, 10, 15]]

    added, skipped = await service._bulk_upsert_auction_events(db_session, dicts)
    await db_session.flush()

    assert added == 3
    assert skipped == 0
    result = await db_session.execute(select(AuctionEvent))
    assert len(result.scalars().all()) == 3


@pytest.mark.asyncio
async def test_bulk_upsert_deduplicates_existing(db_session: AsyncSession) -> None:
    """Running bulk upsert twice produces no duplicates."""
    service = _make_service()
    dicts = [_make_event_dict(date.today() + timedelta(days=d)) for d in [5, 10]]

    await service._bulk_upsert_auction_events(db_session, dicts)
    await db_session.flush()
    added2, skipped2 = await service._bulk_upsert_auction_events(db_session, dicts)
    await db_session.flush()

    assert added2 == 0
    assert skipped2 == 2
    result = await db_session.execute(select(AuctionEvent))
    assert len(result.scalars().all()) == 2


# ─── _link_auctions_to_events ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_auctions_sets_fk(db_session: AsyncSession) -> None:
    """Auction rows whose auction_date matches an AuctionEvent get their FK set."""
    service = _make_service()
    future = date.today() + timedelta(days=20)

    event = await _seed_event(db_session, future)
    auction = await _seed_auction(
        db_session, auction_date=future, auction_event_id=None
    )

    count = await service._link_auctions_to_events(db_session)
    await db_session.flush()

    assert count == 1
    await db_session.refresh(auction)
    assert auction.auction_event_id == event.id


@pytest.mark.asyncio
async def test_link_auctions_skips_already_linked(db_session: AsyncSession) -> None:
    """Auction rows that already have auction_event_id set are not re-linked."""
    service = _make_service()
    future = date.today() + timedelta(days=20)

    event = await _seed_event(db_session, future)
    await _seed_auction(
        db_session, auction_date=future, auction_event_id=event.id
    )

    count = await service._link_auctions_to_events(db_session)

    assert count == 0  # nothing new to link


@pytest.mark.asyncio
async def test_link_auctions_ignores_unmatched_dates(db_session: AsyncSession) -> None:
    """Auctions whose date has no AuctionEvent keep auction_event_id=NULL."""
    service = _make_service()
    future_no_event = date.today() + timedelta(days=25)

    auction = await _seed_auction(
        db_session, auction_date=future_no_event, auction_event_id=None
    )

    count = await service._link_auctions_to_events(db_session)

    assert count == 0
    await db_session.refresh(auction)
    assert auction.auction_event_id is None


# ─── _mark_cancelled_events ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_cancelled_flags_vanished_future_event(
    db_session: AsyncSession,
) -> None:
    """A future AuctionEvent absent from the live calendar is marked cancelled."""
    service = _make_service()
    future = date.today() + timedelta(days=30)
    event = await _seed_event(db_session, future)

    # live calendar returns no events — this date has vanished
    cancelled = await service._mark_cancelled_events(db_session, set())
    await db_session.flush()

    assert cancelled == 1
    await db_session.refresh(event)
    assert event.is_cancelled is True


@pytest.mark.asyncio
async def test_mark_cancelled_ignores_past_events(db_session: AsyncSession) -> None:
    """Past AuctionEvents that are not on the live calendar are NOT cancelled.

    The live calendar only shows future events; a past event not appearing is expected.
    """
    service = _make_service()
    past = date.today() - timedelta(days=30)
    event = await _seed_event(db_session, past)

    cancelled = await service._mark_cancelled_events(db_session, set())
    await db_session.flush()

    assert cancelled == 0
    await db_session.refresh(event)
    assert event.is_cancelled is False


@pytest.mark.asyncio
async def test_mark_cancelled_leaves_present_events_alone(
    db_session: AsyncSession,
) -> None:
    """Future events that ARE in the live calendar remain untouched."""
    service = _make_service()
    future = date.today() + timedelta(days=10)
    event = await _seed_event(db_session, future)

    # live calendar still has this date
    cancelled = await service._mark_cancelled_events(db_session, {future})
    await db_session.flush()

    assert cancelled == 0
    await db_session.refresh(event)
    assert event.is_cancelled is False


@pytest.mark.asyncio
async def test_mark_cancelled_does_not_double_cancel(db_session: AsyncSession) -> None:
    """Already-cancelled events are not counted again on re-runs."""
    service = _make_service()
    future = date.today() + timedelta(days=10)
    await _seed_event(db_session, future, is_cancelled=True)

    cancelled = await service._mark_cancelled_events(db_session, set())
    await db_session.flush()

    # Already cancelled — should not increment the count again
    assert cancelled == 0
