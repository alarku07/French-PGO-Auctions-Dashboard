"""Stats and chart endpoints.

GET /api/v1/stats           — aggregate dashboard statistics
GET /api/v1/charts/prices   — price time-series data
GET /api/v1/charts/volumes  — volume time-series data
"""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.auction import Auction
from app.models.sync_log import SyncLog
from app.schemas.auction import (
    PriceChartDataPoint,
    PriceChartFilters,
    PriceChartResponse,
    StatsResponse,
    VolumeChartDataPoint,
    VolumeChartFilters,
    VolumeChartResponse,
)

router = APIRouter()

_VALID_AGGREGATIONS = {"per_auction", "monthly", "yearly"}


def _five_years_ago() -> date:
    today = date.today()
    return today.replace(year=today.year - 5)


def _parse_date_param(value: str | None, param_name: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": (
                        f"Invalid date format for {param_name}. Expected YYYY-MM-DD."
                    ),
                    "details": None,
                }
            },
        ) from None


@router.get("/stats", response_model=StatsResponse, summary="Aggregate statistics")
async def get_stats(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> StatsResponse:
    # Total auctions held: COUNT(DISTINCT auction_date) WHERE status='past'
    count_result = await session.execute(
        select(func.count(distinct(Auction.auction_date))).where(
            Auction.status == "past"
        )
    )
    total_auctions_held = count_result.scalar_one() or 0

    # Total volume: SUM(volume_allocated_mwh) WHERE past AND technology IS NULL
    volume_result = await session.execute(
        select(func.sum(Auction.volume_allocated_mwh)).where(
            Auction.status == "past",
            Auction.technology.is_(None),        )
    )
    total_volume = volume_result.scalar_one()

    # Weighted avg price
    wavg_result = await session.execute(
        select(
            func.sum(Auction.weighted_avg_price_eur * Auction.volume_allocated_mwh),
            func.sum(Auction.volume_allocated_mwh),
        ).where(
            Auction.status == "past",
            Auction.technology.is_(None),
            Auction.volume_allocated_mwh.isnot(None),
            Auction.weighted_avg_price_eur.isnot(None),
        )
    )
    wavg_row = wavg_result.one()
    numerator, denominator = wavg_row[0], wavg_row[1]
    overall_wavg = (
        Decimal(str(numerator)) / Decimal(str(denominator))
        if denominator
        else None
    )

    # Last updated: MAX(completed_at) from sync_log WHERE outcome='success'
    last_updated_result = await session.execute(
        select(func.max(SyncLog.completed_at)).where(SyncLog.outcome == "success")
    )
    last_updated = last_updated_result.scalar_one()

    return StatsResponse(
        total_auctions_held=total_auctions_held,
        total_volume_awarded_mwh=total_volume,
        overall_weighted_avg_price_eur=overall_wavg,
        last_updated=last_updated,
    )


@router.get(
    "/charts/prices",
    response_model=PriceChartResponse,
    summary="Price time-series for chart",
)
async def get_chart_prices(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    region: str | None = Query(None),
    technology: str | None = Query(None),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PriceChartResponse:
    start = _parse_date_param(start_date, "start_date") or _five_years_ago()
    end = _parse_date_param(end_date, "end_date") or date.today()

    stmt = (
        select(
            Auction.auction_date,
            Auction.region,
            Auction.weighted_avg_price_eur,
            Auction.volume_allocated_mwh,
        )
        .where(
            Auction.status == "past",
            Auction.auction_date >= start,
            Auction.auction_date <= end,
        )
        .order_by(Auction.auction_date.asc())
    )

    if region:
        stmt = stmt.where(Auction.region == region)
    if technology:
        stmt = stmt.where(Auction.technology == technology)
    else:
        # Default: return aggregate rows (technology IS NULL) for cleaner chart
        stmt = stmt.where(Auction.technology.is_(None))
    result = await session.execute(stmt)
    rows = result.all()

    data = [
        PriceChartDataPoint(
            auction_date=row.auction_date,
            region=row.region,
            weighted_avg_price_eur=row.weighted_avg_price_eur,
            volume_allocated_mwh=row.volume_allocated_mwh,
        )
        for row in rows
    ]

    return PriceChartResponse(
        data=data,
        filters=PriceChartFilters(
            start_date=start,
            end_date=end,
            region=region,
            technology=technology,
        ),
    )


@router.get(
    "/charts/volumes",
    response_model=VolumeChartResponse,
    summary="Volume time-series for chart",
)
async def get_chart_volumes(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    region: str | None = Query(None),
    technology: str | None = Query(None),
    aggregation: str = Query("per_auction"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> VolumeChartResponse:
    if aggregation not in _VALID_AGGREGATIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid aggregation '{aggregation}'. "
                    f"Allowed: {sorted(_VALID_AGGREGATIONS)}",
                    "details": None,
                }
            },
        )

    start = _parse_date_param(start_date, "start_date") or _five_years_ago()
    end = _parse_date_param(end_date, "end_date") or date.today()

    base_filter = [
        Auction.status == "past",
        Auction.auction_date >= start,
        Auction.auction_date <= end,
    ]

    if technology:
        base_filter.append(Auction.technology == technology)
    else:
        base_filter.append(Auction.technology.is_(None))
    if region:
        base_filter.append(Auction.region == region)

    data: list[VolumeChartDataPoint] = []

    if aggregation == "per_auction":
        stmt = (
            select(
                Auction.auction_date,
                Auction.region,
                Auction.volume_offered_mwh,
                Auction.volume_allocated_mwh,
            )
            .where(*base_filter)
            .order_by(Auction.auction_date.asc())
        )
        result = await session.execute(stmt)
        data = [
            VolumeChartDataPoint(
                period=str(row.auction_date),
                region=row.region,
                volume_offered_mwh=row.volume_offered_mwh,
                volume_allocated_mwh=row.volume_allocated_mwh,
            )
            for row in result.all()
        ]

    elif aggregation == "monthly":
        # Group by YYYY-MM — use strftime for SQLite compat; PostgreSQL uses to_char
        # Use Python-side grouping for portability across SQLite (tests) and PostgreSQL
        stmt = (
            select(
                Auction.auction_date,
                Auction.region,
                Auction.volume_offered_mwh,
                Auction.volume_allocated_mwh,
            )
            .where(*base_filter)
            .order_by(Auction.auction_date.asc())
        )
        result = await session.execute(stmt)
        rows = result.all()

        monthly: dict[tuple[str, str], dict[str, Decimal | None]] = {}
        for row in rows:
            period_key = row.auction_date.strftime("%Y-%m")
            region_key = row.region
            key = (period_key, region_key)
            if key not in monthly:
                monthly[key] = {"offered": Decimal(0), "allocated": Decimal(0)}
            if row.volume_offered_mwh:
                offered = monthly[key]["offered"]
                monthly[key]["offered"] = (
                    (offered or Decimal(0)) + row.volume_offered_mwh
                )
            if row.volume_allocated_mwh:
                alloc = monthly[key]["allocated"]
                monthly[key]["allocated"] = (
                    (alloc or Decimal(0)) + row.volume_allocated_mwh
                )

        data = [
            VolumeChartDataPoint(
                period=key[0],
                region=key[1],
                volume_offered_mwh=vals["offered"],
                volume_allocated_mwh=vals["allocated"],
            )
            for key, vals in sorted(monthly.items())
        ]

    else:  # yearly
        stmt = (
            select(
                Auction.auction_date,
                Auction.region,
                Auction.volume_offered_mwh,
                Auction.volume_allocated_mwh,
            )
            .where(*base_filter)
            .order_by(Auction.auction_date.asc())
        )
        result = await session.execute(stmt)
        rows = result.all()

        yearly: dict[tuple[str, str], dict[str, Decimal | None]] = {}
        for row in rows:
            period_key = str(row.auction_date.year)
            region_key = row.region
            key = (period_key, region_key)
            if key not in yearly:
                yearly[key] = {"offered": Decimal(0), "allocated": Decimal(0)}
            if row.volume_offered_mwh:
                offered = yearly[key]["offered"]
                yearly[key]["offered"] = (
                    (offered or Decimal(0)) + row.volume_offered_mwh
                )
            if row.volume_allocated_mwh:
                alloc = yearly[key]["allocated"]
                yearly[key]["allocated"] = (
                    (alloc or Decimal(0)) + row.volume_allocated_mwh
                )

        data = [
            VolumeChartDataPoint(
                period=key[0],
                region=key[1],
                volume_offered_mwh=vals["offered"],
                volume_allocated_mwh=vals["allocated"],
            )
            for key, vals in sorted(yearly.items())
        ]

    return VolumeChartResponse(
        data=data,
        filters=VolumeChartFilters(
            start_date=start,
            end_date=end,
            region=region,
            technology=technology,
            aggregation=aggregation,
        ),
    )
