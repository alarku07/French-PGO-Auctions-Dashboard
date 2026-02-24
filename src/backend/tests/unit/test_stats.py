"""Smoke tests for aggregate statistics computation (FR-004).

Verifies that total_auctions_held, total_volume_awarded_mwh, and
overall_weighted_avg_price_eur are computed correctly from known data.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction


async def _seed(session: AsyncSession, records: list[dict]) -> None:
    """Insert a list of auction dicts."""
    for data in records:
        session.add(Auction(**data))
    await session.flush()


async def _compute_stats(session: AsyncSession) -> dict:  # type: ignore[type-arg]
    """Replicate the stats query logic from GET /api/v1/stats."""
    # Total auctions held: DISTINCT auction_date WHERE status='past'
    count_result = await session.execute(
        select(func.count(func.distinct(Auction.auction_date))).where(
            Auction.status == "past"
        )
    )
    total_auctions_held = count_result.scalar_one()

    # Total volume awarded: SUM WHERE status='past' AND technology IS NULL
    volume_result = await session.execute(
        select(func.sum(Auction.volume_allocated_mwh)).where(
            Auction.status == "past",
            Auction.technology.is_(None),  # type: ignore[union-attr]
        )
    )
    total_volume = volume_result.scalar_one()

    # Weighted average price: SUM(price * volume) / SUM(volume) WHERE past AND technology IS NULL
    wavg_result = await session.execute(
        select(
            func.sum(Auction.weighted_avg_price_eur * Auction.volume_allocated_mwh),
            func.sum(Auction.volume_allocated_mwh),
        ).where(
            Auction.status == "past",
            Auction.technology.is_(None),  # type: ignore[union-attr]
            Auction.volume_allocated_mwh.isnot(None),  # type: ignore[union-attr]
            Auction.weighted_avg_price_eur.isnot(None),  # type: ignore[union-attr]
        )
    )
    row = wavg_result.one()
    numerator, denominator = row[0], row[1]
    overall_wavg = (numerator / denominator) if denominator else None

    return {
        "total_auctions_held": total_auctions_held,
        "total_volume_awarded_mwh": total_volume,
        "overall_weighted_avg_price_eur": overall_wavg,
    }


@pytest.mark.asyncio
async def test_stats_empty_database(db_session: AsyncSession) -> None:
    """Stats on an empty database return zero/None values."""
    stats = await _compute_stats(db_session)
    assert stats["total_auctions_held"] == 0
    assert stats["total_volume_awarded_mwh"] is None
    assert stats["overall_weighted_avg_price_eur"] is None


@pytest.mark.asyncio
async def test_total_auctions_held_counts_distinct_dates(db_session: AsyncSession) -> None:
    """total_auctions_held counts distinct auction dates, not total rows."""
    await _seed(
        db_session,
        [
            # Two regions on the same date = 1 auction event
            {
                "auction_date": date(2025, 11, 18),
                "region": "Bretagne",
                "production_period": "2025-08",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("100000"),
                "volume_allocated_mwh": Decimal("90000"),
                "weighted_avg_price_eur": Decimal("0.30"),
            },
            {
                "auction_date": date(2025, 11, 18),
                "region": "Normandie",
                "production_period": "2025-08",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("80000"),
                "volume_allocated_mwh": Decimal("70000"),
                "weighted_avg_price_eur": Decimal("0.32"),
            },
            # Different date = 2nd auction event
            {
                "auction_date": date(2025, 10, 21),
                "region": "Bretagne",
                "production_period": "2025-07",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("95000"),
                "volume_allocated_mwh": Decimal("85000"),
                "weighted_avg_price_eur": Decimal("0.28"),
            },
        ],
    )
    stats = await _compute_stats(db_session)
    assert stats["total_auctions_held"] == 2  # 2 distinct dates


@pytest.mark.asyncio
async def test_total_volume_excludes_technology_rows(db_session: AsyncSession) -> None:
    """total_volume_awarded_mwh sums only technology=NULL rows (aggregate level)."""
    await _seed(
        db_session,
        [
            # Aggregate row (technology IS NULL) — should be included
            {
                "auction_date": date(2025, 11, 18),
                "region": "Bretagne",
                "production_period": "2025-08",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("100000"),
                "volume_allocated_mwh": Decimal("90000"),
                "weighted_avg_price_eur": Decimal("0.30"),
            },
            # Technology breakdown row — should be excluded from sum
            {
                "auction_date": date(2025, 11, 18),
                "region": "Bretagne",
                "production_period": "2025-08",
                "technology": "Wind",
                "status": "past",
                "volume_offered_mwh": Decimal("60000"),
                "volume_allocated_mwh": Decimal("55000"),
                "weighted_avg_price_eur": Decimal("0.28"),
            },
        ],
    )
    stats = await _compute_stats(db_session)
    assert stats["total_volume_awarded_mwh"] == Decimal("90000")


@pytest.mark.asyncio
async def test_weighted_average_price_correctness(db_session: AsyncSession) -> None:
    """overall_weighted_avg_price_eur is the volume-weighted mean."""
    # Region A: 90,000 MWh at €0.30 → contribution: 27,000
    # Region B: 70,000 MWh at €0.40 → contribution: 28,000
    # Weighted avg = (27000 + 28000) / (90000 + 70000) = 55000/160000 = 0.34375
    await _seed(
        db_session,
        [
            {
                "auction_date": date(2025, 11, 18),
                "region": "Bretagne",
                "production_period": "2025-08",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("100000"),
                "volume_allocated_mwh": Decimal("90000"),
                "weighted_avg_price_eur": Decimal("0.30"),
            },
            {
                "auction_date": date(2025, 11, 18),
                "region": "Normandie",
                "production_period": "2025-08",
                "technology": None,
                "status": "past",
                "volume_offered_mwh": Decimal("80000"),
                "volume_allocated_mwh": Decimal("70000"),
                "weighted_avg_price_eur": Decimal("0.40"),
            },
        ],
    )
    stats = await _compute_stats(db_session)
    expected = Decimal("55000") / Decimal("160000")
    assert stats["overall_weighted_avg_price_eur"] is not None
    assert abs(stats["overall_weighted_avg_price_eur"] - expected) < Decimal("0.0001")


@pytest.mark.asyncio
async def test_upcoming_auctions_excluded_from_stats(db_session: AsyncSession) -> None:
    """Upcoming auctions should not appear in any statistic."""
    await _seed(
        db_session,
        [
            {
                "auction_date": date(2026, 3, 18),
                "region": "Bretagne",
                "production_period": "2025-12",
                "technology": None,
                "status": "upcoming",
                "volume_offered_mwh": None,
                "volume_allocated_mwh": None,
                "weighted_avg_price_eur": None,
            },
        ],
    )
    stats = await _compute_stats(db_session)
    assert stats["total_auctions_held"] == 0
    assert stats["total_volume_awarded_mwh"] is None
