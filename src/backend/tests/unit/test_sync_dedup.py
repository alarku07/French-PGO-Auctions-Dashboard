"""Smoke tests for sync deduplication logic (FR-016).

Tests that duplicate auction records are skipped based on the composite key
(auction_date, region, production_period, technology) and that existing
non-NULL fields are never overwritten.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction


async def _insert_auction(session: AsyncSession, **kwargs) -> Auction:  # type: ignore[no-untyped-def]
    """Helper: insert a single auction record and flush."""
    auction = Auction(**kwargs)
    session.add(auction)
    await session.flush()
    return auction


async def _upsert_auction(session: AsyncSession, data: dict) -> tuple[str, Auction]:  # type: ignore[no-untyped-def]
    """Minimal upsert logic matching the sync service contract.

    Returns ("added"|"skipped"|"updated", auction).
    """
    stmt = select(Auction).where(
        Auction.auction_date == data["auction_date"],
        Auction.region == data["region"],
        Auction.production_period == data["production_period"],
        Auction.technology == data.get("technology"),
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is None:
        new_record = Auction(**data)
        session.add(new_record)
        await session.flush()
        return ("added", new_record)

    # Fill in NULL fields only — never overwrite non-NULL values
    changed = False
    for field, value in data.items():
        if field in ("auction_date", "region", "production_period", "technology"):
            continue  # natural key fields — never update
        current = getattr(existing, field, None)
        if current is None and value is not None:
            setattr(existing, field, value)
            changed = True

    if changed:
        await session.flush()
        return ("updated", existing)

    return ("skipped", existing)


@pytest.mark.asyncio
async def test_insert_new_record(db_session: AsyncSession) -> None:
    """A new auction record is inserted successfully."""
    outcome, record = await _upsert_auction(
        db_session,
        {
            "auction_date": date(2025, 11, 18),
            "region": "Bretagne",
            "production_period": "2025-08",
            "technology": None,
            "status": "past",
            "volume_offered_mwh": Decimal("100000"),
            "volume_allocated_mwh": Decimal("95000"),
            "weighted_avg_price_eur": Decimal("0.34"),
        },
    )
    assert outcome == "added"
    assert record.id is not None
    assert record.volume_allocated_mwh == Decimal("95000")


@pytest.mark.asyncio
async def test_exact_duplicate_is_skipped(db_session: AsyncSession) -> None:
    """An exact duplicate record (same composite key + same values) is skipped."""
    data = {
        "auction_date": date(2025, 11, 18),
        "region": "Bretagne",
        "production_period": "2025-08",
        "technology": None,
        "status": "past",
        "volume_offered_mwh": Decimal("100000"),
        "volume_allocated_mwh": Decimal("95000"),
        "weighted_avg_price_eur": Decimal("0.34"),
    }
    await _upsert_auction(db_session, data)
    outcome, _ = await _upsert_auction(db_session, data)
    assert outcome == "skipped"

    # Only one record should exist
    result = await db_session.execute(select(Auction))
    records = result.scalars().all()
    assert len(records) == 1


@pytest.mark.asyncio
async def test_existing_nonnull_field_not_overwritten(db_session: AsyncSession) -> None:
    """An existing non-NULL field must not be overwritten by an incoming record."""
    original_price = Decimal("0.34")
    await _upsert_auction(
        db_session,
        {
            "auction_date": date(2025, 11, 18),
            "region": "Bretagne",
            "production_period": "2025-08",
            "technology": None,
            "status": "past",
            "volume_offered_mwh": Decimal("100000"),
            "volume_allocated_mwh": Decimal("95000"),
            "weighted_avg_price_eur": original_price,
        },
    )

    # Try to overwrite with a different price
    outcome, record = await _upsert_auction(
        db_session,
        {
            "auction_date": date(2025, 11, 18),
            "region": "Bretagne",
            "production_period": "2025-08",
            "technology": None,
            "status": "past",
            "volume_offered_mwh": Decimal("100000"),
            "volume_allocated_mwh": Decimal("95000"),
            "weighted_avg_price_eur": Decimal("0.99"),  # different!
        },
    )
    assert outcome == "skipped"
    assert record.weighted_avg_price_eur == original_price  # unchanged


@pytest.mark.asyncio
async def test_null_field_filled_by_incoming_record(db_session: AsyncSession) -> None:
    """A NULL field in an existing record is filled in by an incoming record."""
    await _upsert_auction(
        db_session,
        {
            "auction_date": date(2025, 11, 18),
            "region": "Bretagne",
            "production_period": "2025-08",
            "technology": None,
            "status": "past",
            "volume_offered_mwh": Decimal("100000"),
            "volume_allocated_mwh": None,  # missing field
            "weighted_avg_price_eur": None,  # missing field
        },
    )

    outcome, record = await _upsert_auction(
        db_session,
        {
            "auction_date": date(2025, 11, 18),
            "region": "Bretagne",
            "production_period": "2025-08",
            "technology": None,
            "status": "past",
            "volume_offered_mwh": Decimal("100000"),
            "volume_allocated_mwh": Decimal("95000"),  # now available
            "weighted_avg_price_eur": Decimal("0.34"),  # now available
        },
    )
    assert outcome == "updated"
    assert record.volume_allocated_mwh == Decimal("95000")
    assert record.weighted_avg_price_eur == Decimal("0.34")


@pytest.mark.asyncio
async def test_different_technology_creates_separate_record(db_session: AsyncSession) -> None:
    """Records with same date/region/period but different technology are distinct."""
    common = {
        "auction_date": date(2025, 11, 18),
        "region": "Bretagne",
        "production_period": "2025-08",
        "status": "past",
        "volume_offered_mwh": Decimal("50000"),
        "volume_allocated_mwh": Decimal("48000"),
        "weighted_avg_price_eur": Decimal("0.30"),
    }
    outcome1, _ = await _upsert_auction(db_session, {**common, "technology": "Wind"})
    outcome2, _ = await _upsert_auction(db_session, {**common, "technology": "Solar"})
    outcome3, _ = await _upsert_auction(db_session, {**common, "technology": "Wind"})  # dup

    assert outcome1 == "added"
    assert outcome2 == "added"
    assert outcome3 == "skipped"

    result = await db_session.execute(select(Auction))
    records = result.scalars().all()
    assert len(records) == 2
