"""Auction endpoints.

GET /api/v1/auctions          — past results with pagination + filtering
GET /api/v1/auctions/upcoming — upcoming scheduled auctions
GET /api/v1/regions           — distinct regions in dataset
GET /api/v1/technologies      — distinct technologies in dataset
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.auction import Auction
from app.schemas.auction import (
    AuctionListResponse,
    AuctionResponse,
    PaginationMeta,
    RegionListResponse,
    TechnologyListResponse,
    UpcomingAuctionListResponse,
    UpcomingAuctionResponse,
)

router = APIRouter()

_VALID_SORT_FIELDS = {
    "auction_date",
    "region",
    "volume_allocated_mwh",
    "weighted_avg_price_eur",
}


def _previous_month_range() -> tuple[date, date]:
    """Return (first_day, last_day) of the previous calendar month."""
    today = date.today()
    first_of_this_month = today.replace(day=1)
    last_of_prev = first_of_this_month - timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev, last_of_prev


def _parse_date(value: str | None, param_name: str) -> date | None:
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


@router.get(
    "/auctions",
    response_model=AuctionListResponse,
    summary="List past auctions",
)
async def list_auctions(
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    region: str | None = Query(None),
    technology: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
    sort_by: str = Query("auction_date"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AuctionListResponse:
    if page_size > 200:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "page_size must not exceed 200.",
                    "details": None,
                }
            },
        )

    if sort_by not in _VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Invalid sort_by field '{sort_by}'. "
                    f"Allowed: {sorted(_VALID_SORT_FIELDS)}",
                    "details": None,
                }
            },
        )

    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    if start is None and end is None:
        start, end = _previous_month_range()

    # Base query
    stmt = select(Auction).where(Auction.status == "past")
    count_stmt = (
        select(func.count()).select_from(Auction).where(Auction.status == "past")
    )

    if start:
        stmt = stmt.where(Auction.auction_date >= start)
        count_stmt = count_stmt.where(Auction.auction_date >= start)
    if end:
        stmt = stmt.where(Auction.auction_date <= end)
        count_stmt = count_stmt.where(Auction.auction_date <= end)
    if region:
        stmt = stmt.where(Auction.region == region)
        count_stmt = count_stmt.where(Auction.region == region)
    if technology:
        stmt = stmt.where(Auction.technology == technology)
        count_stmt = count_stmt.where(Auction.technology == technology)
    else:
        # No technology selected: show only aggregate rows (technology IS NULL)
        # so each (date, region) appears exactly once.
        stmt = stmt.where(Auction.technology.is_(None))
        count_stmt = count_stmt.where(Auction.technology.is_(None))

    # Sorting — region asc as deterministic tiebreaker
    sort_col = getattr(Auction, sort_by)
    stmt = stmt.order_by(
        sort_col.desc() if sort_order == "desc" else sort_col.asc(),
        Auction.region.asc(),
    )

    # Total count
    total_result = await session.execute(count_stmt)
    total_items = total_result.scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    auctions = result.scalars().all()

    total_pages = max(1, -(-total_items // page_size))  # ceiling division

    return AuctionListResponse(
        data=[AuctionResponse.model_validate(a) for a in auctions],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/auctions/upcoming",
    response_model=UpcomingAuctionListResponse,
    summary="List upcoming auctions",
)
async def list_upcoming_auctions(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> UpcomingAuctionListResponse:
    stmt = (
        select(Auction)
        .where(Auction.status == "upcoming")
        .order_by(Auction.auction_date.asc())
    )
    result = await session.execute(stmt)
    auctions = result.scalars().all()

    return UpcomingAuctionListResponse(
        data=[UpcomingAuctionResponse.model_validate(a) for a in auctions],
        count=len(auctions),
    )


@router.get(
    "/regions",
    response_model=RegionListResponse,
    summary="List available regions",
)
async def list_regions(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RegionListResponse:
    stmt = select(distinct(Auction.region)).order_by(Auction.region.asc())
    result = await session.execute(stmt)
    regions = [row[0] for row in result.all()]
    return RegionListResponse(data=regions)


@router.get(
    "/technologies",
    response_model=TechnologyListResponse,
    summary="List available technology types",
)
async def list_technologies(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> TechnologyListResponse:
    stmt = (
        select(distinct(Auction.technology))
        .where(Auction.technology.isnot(None))
        .order_by(Auction.technology.asc())
    )
    result = await session.execute(stmt)
    technologies = [row[0] for row in result.all()]
    return TechnologyListResponse(data=technologies)
