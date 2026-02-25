"""Smoke tests for API input validation and empty-state handling.

Uses FastAPI TestClient (via httpx) with an in-memory SQLite database.
Verifies: 400 on bad inputs, 200 with empty list when no data.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint returns 200 or 503 (depends on DB availability)."""
    response = await client.get("/api/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_auctions_invalid_date_format_returns_400(client: AsyncClient) -> None:
    """GET /auctions with invalid date format returns 400."""
    response = await client.get("/api/v1/auctions", params={"start_date": "not-a-date"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_auctions_page_size_too_large_returns_400(client: AsyncClient) -> None:
    """GET /auctions with page_size > 200 returns 400."""
    response = await client.get("/api/v1/auctions", params={"page_size": 999})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upcoming_empty_returns_200(client: AsyncClient) -> None:
    """GET /auctions/upcoming on empty DB returns 200 with empty list."""
    response = await client.get("/api/v1/auctions/upcoming")
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_auctions_empty_returns_200(client: AsyncClient) -> None:
    """GET /auctions on empty DB returns 200 with empty data and valid pagination."""
    response = await client.get("/api/v1/auctions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert "pagination" in data


@pytest.mark.asyncio
async def test_stats_empty_db_returns_200(client: AsyncClient) -> None:
    """GET /stats on empty DB returns 200 with zero/null values."""
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_auctions_held"] == 0
    assert data["last_updated"] is None


@pytest.mark.asyncio
async def test_regions_empty_returns_200(client: AsyncClient) -> None:
    """GET /regions on empty DB returns 200 with empty list."""
    response = await client.get("/api/v1/regions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_technologies_empty_returns_200(client: AsyncClient) -> None:
    """GET /technologies on empty DB returns 200 with empty list."""
    response = await client.get("/api/v1/technologies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
