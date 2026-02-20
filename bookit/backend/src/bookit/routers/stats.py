"""Statistics router — booking KPIs for a tenant."""

import aiosqlite
from fastapi import APIRouter, Depends, Query

from src.bookit.database import get_db
from src.bookit.schemas.stats import StatsResponse
from src.bookit.services.stats_service import get_tenant_stats

router = APIRouter(tags=["stats"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


@router.get("/tenants/{slug}/stats", response_model=StatsResponse)
async def tenant_stats(
    slug: str,
    period: str = Query(default="month", pattern="^(week|month|year)$"),
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> StatsResponse:
    """Get booking statistics for a tenant."""
    return await get_tenant_stats(db, slug, period)
