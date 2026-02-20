"""Statistics aggregation service."""

from datetime import UTC, datetime, timedelta

import aiosqlite
from fastapi import HTTPException

from src.bookit.schemas.stats import ServiceStats, StatsResponse

_PERIOD_DAYS = {
    "week": 7,
    "month": 30,
    "year": 365,
}


async def get_tenant_stats(
    db: aiosqlite.Connection,
    slug: str,
    period: str = "month",
) -> StatsResponse:
    """Compute booking statistics for a tenant within a time period.

    Args:
        db: Open database connection.
        slug: Tenant slug.
        period: One of ``week``, ``month``, ``year``.

    Returns:
        Aggregated stats.
    """
    if period not in _PERIOD_DAYS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    # Resolve tenant
    cursor = await db.execute("SELECT id FROM tenants WHERE slug = ?", (slug,))
    tenant_row = await cursor.fetchone()
    if tenant_row is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    tenant_id = tenant_row["id"]

    since = datetime.now(UTC) - timedelta(days=_PERIOD_DAYS[period])
    since_str = since.isoformat()

    # Total bookings
    cursor = await db.execute(
        "SELECT COUNT(*) AS cnt FROM bookings b "
        "JOIN slots sl ON b.slot_id = sl.id "
        "JOIN services svc ON sl.service_id = svc.id "
        "WHERE svc.tenant_id = ? AND b.created_at >= ?",
        (tenant_id, since_str),
    )
    total_row = await cursor.fetchone()
    total_bookings = total_row["cnt"]

    # Confirmed
    cursor = await db.execute(
        "SELECT COUNT(*) AS cnt FROM bookings b "
        "JOIN slots sl ON b.slot_id = sl.id "
        "JOIN services svc ON sl.service_id = svc.id "
        "WHERE svc.tenant_id = ? AND b.created_at >= ? AND b.status = 'confirmed'",
        (tenant_id, since_str),
    )
    confirmed_row = await cursor.fetchone()
    confirmed = confirmed_row["cnt"]

    cancelled = total_bookings - confirmed

    # Revenue (only confirmed + paid, or confirmed for free services)
    cursor = await db.execute(
        "SELECT COALESCE(SUM(svc.price_cents), 0) AS rev FROM bookings b "
        "JOIN slots sl ON b.slot_id = sl.id "
        "JOIN services svc ON sl.service_id = svc.id "
        "WHERE svc.tenant_id = ? AND b.created_at >= ? AND b.status = 'confirmed'",
        (tenant_id, since_str),
    )
    rev_row = await cursor.fetchone()
    total_revenue = rev_row["rev"]

    # Per-service breakdown
    cursor = await db.execute(
        "SELECT svc.id AS service_id, svc.name AS service_name, "
        "COUNT(b.id) AS booking_count, "
        "COALESCE(SUM(svc.price_cents), 0) AS revenue_cents "
        "FROM bookings b "
        "JOIN slots sl ON b.slot_id = sl.id "
        "JOIN services svc ON sl.service_id = svc.id "
        "WHERE svc.tenant_id = ? AND b.created_at >= ? AND b.status = 'confirmed' "
        "GROUP BY svc.id ORDER BY booking_count DESC",
        (tenant_id, since_str),
    )
    svc_rows = await cursor.fetchall()

    services = [
        ServiceStats(
            service_id=r["service_id"],
            service_name=r["service_name"],
            booking_count=r["booking_count"],
            revenue_cents=r["revenue_cents"],
        )
        for r in svc_rows
    ]

    return StatsResponse(
        total_bookings=total_bookings,
        confirmed_bookings=confirmed,
        cancelled_bookings=cancelled,
        total_revenue_cents=total_revenue,
        services=services,
        period=period,
    )
