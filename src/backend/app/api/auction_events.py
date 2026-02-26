"""AuctionEvent endpoints.

GET /api/v1/auction-events — list auction events with associated auctions
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.auction_event import AuctionEvent
from app.schemas.auction_event import (
    AuctionEventListResponse,
    AuctionEventResponse,
    AuctionSummary,
)

router = APIRouter()


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


def _compute_status(event_date: date) -> str:
    """Compute display status from the event date relative to today."""
    return "upcoming" if event_date >= date.today() else "completed"


@router.get(
    "/auction-events",
    response_model=AuctionEventListResponse,
    summary="List auction events",
)
async def list_auction_events(
    include_cancelled: bool = Query(
        False, description="Include events marked as cancelled"
    ),
    start_date: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> AuctionEventListResponse:
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    stmt = (
        select(AuctionEvent)
        .options(selectinload(AuctionEvent.auctions))
        .order_by(AuctionEvent.event_date.desc())
    )

    if not include_cancelled:
        stmt = stmt.where(AuctionEvent.is_cancelled.is_(False))
    if start:
        stmt = stmt.where(AuctionEvent.event_date >= start)
    if end:
        stmt = stmt.where(AuctionEvent.event_date <= end)

    result = await session.execute(stmt)
    events = result.scalars().all()

    response_items = [
        AuctionEventResponse(
            id=event.id,
            event_date=event.event_date,
            status=_compute_status(event.event_date),
            is_cancelled=event.is_cancelled,
            auctioning_month=event.auctioning_month,
            production_month=event.production_month,
            order_book_open=event.order_book_open,
            cash_trading_limits_modification=event.cash_trading_limits_modification,
            order_book_close=event.order_book_close,
            order_matching=event.order_matching,
            auctions=[AuctionSummary.model_validate(a) for a in event.auctions],
        )
        for event in events
    ]

    return AuctionEventListResponse(data=response_items, count=len(response_items))
