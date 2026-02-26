from fastapi import APIRouter

from app.api import auction_events, auctions, stats

api_router = APIRouter(prefix="/api/v1")

# Auction event endpoints
api_router.include_router(auction_events.router, tags=["auction-events"])

# Auction endpoints
api_router.include_router(auctions.router, tags=["auctions"])

# Stats and chart endpoints
api_router.include_router(stats.router, tags=["stats"])


@api_router.get("/health", summary="Health check")
async def health_check() -> dict:  # type: ignore[type-arg]
    """Return service health status."""
    from sqlalchemy import text

    from app.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(  # type: ignore[return-value]
            status_code=503,
            content={"status": "degraded", "database": "unreachable"},
        )
