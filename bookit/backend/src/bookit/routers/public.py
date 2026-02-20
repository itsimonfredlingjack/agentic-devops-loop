"""Public booking router — unauthenticated endpoint for the booking page."""

from datetime import UTC, datetime, timedelta

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from src.bookit.database import get_db
from src.bookit.schemas.public import PublicServiceView, PublicSlotView, PublicTenantView

router = APIRouter(prefix="/book", tags=["public"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


@router.get("/{slug}", response_model=PublicTenantView)
async def get_public_booking_page(
    slug: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> PublicTenantView:
    """Return tenant info, services, and available slots for the next 14 days.

    Args:
        slug: Tenant URL slug.
        db: Injected database connection.

    Returns:
        Combined public view with services and available slots.

    Raises:
        HTTPException 404: If no tenant with that slug exists.
    """
    # Look up tenant
    cursor = await db.execute("SELECT * FROM tenants WHERE slug = ?", (slug,))
    tenant = await cursor.fetchone()
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")

    # Fetch services
    cursor = await db.execute(
        "SELECT * FROM services WHERE tenant_id = ? ORDER BY name",
        (tenant["id"],),
    )
    service_rows = await cursor.fetchall()
    services = [
        PublicServiceView(
            id=row["id"],
            name=row["name"],
            duration_min=row["duration_min"],
            capacity=row["capacity"],
        )
        for row in service_rows
    ]

    # Fetch available slots for each service (next 14 days, not fully booked)
    now = datetime.now(tz=UTC).isoformat()
    cutoff = (datetime.now(tz=UTC) + timedelta(days=14)).isoformat()

    slots_by_service: dict[int, list[PublicSlotView]] = {}
    for service in services:
        cursor = await db.execute(
            """
            SELECT * FROM slots
            WHERE service_id = ?
              AND start_time > ?
              AND start_time < ?
              AND booked_count < capacity
            ORDER BY start_time
            """,
            (service.id, now, cutoff),
        )
        slot_rows = await cursor.fetchall()
        slots_by_service[service.id] = [
            PublicSlotView(
                id=row["id"],
                service_id=row["service_id"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                available=row["capacity"] - row["booked_count"],
            )
            for row in slot_rows
        ]

    return PublicTenantView(
        name=tenant["name"],
        slug=tenant["slug"],
        services=services,
        slots_by_service=slots_by_service,
    )
