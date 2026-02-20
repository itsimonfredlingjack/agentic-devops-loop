"""Slots router — create individual slots and bulk-generate daily schedules."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from src.bookit.database import get_db
from src.bookit.schemas.slot import SlotBulkCreate, SlotCreate, SlotRead
from src.bookit.services import slot_service

router = APIRouter(tags=["slots"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


async def _resolve_service(db: aiosqlite.Connection, slug: str, service_id: int) -> int:
    """Validate that a service belongs to the given tenant and return its id.

    Args:
        db: Open database connection.
        slug: Tenant slug.
        service_id: Claimed service primary key.

    Returns:
        The verified service primary key.

    Raises:
        HTTPException 404: If the tenant or service is not found / mismatched.
    """
    cursor = await db.execute("SELECT id FROM tenants WHERE slug = ?", (slug,))
    tenant_row = await cursor.fetchone()
    if tenant_row is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")

    cursor = await db.execute(
        "SELECT id FROM services WHERE id = ? AND tenant_id = ?",
        (service_id, tenant_row["id"]),
    )
    svc_row = await cursor.fetchone()
    if svc_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Service {service_id} not found for tenant '{slug}'",
        )
    return svc_row["id"]


@router.post(
    "/tenants/{slug}/services/{service_id}/slots",
    response_model=SlotRead,
    status_code=201,
)
async def create_slot(
    slug: str,
    service_id: int,
    payload: SlotCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> SlotRead:
    """Create a single slot for a service.

    Args:
        slug: Tenant slug.
        service_id: Service primary key.
        payload: Slot creation payload.
        db: Injected database connection.

    Returns:
        The newly created slot.

    Raises:
        HTTPException 409: If the slot overlaps an existing one.
    """
    svc_id = await _resolve_service(db, slug, service_id)
    return await slot_service.create_slot(
        db, svc_id, payload.start_time, payload.end_time, payload.capacity
    )


@router.post(
    "/tenants/{slug}/services/{service_id}/slots/generate",
    response_model=list[SlotRead],
    status_code=201,
)
async def generate_slots(
    slug: str,
    service_id: int,
    payload: SlotBulkCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> list[SlotRead]:
    """Bulk-generate equally spaced slots for a service on a given day.

    Args:
        slug: Tenant slug.
        service_id: Service primary key.
        payload: Bulk generation parameters.
        db: Injected database connection.

    Returns:
        List of created slots (overlapping slots are silently skipped).
    """
    svc_id = await _resolve_service(db, slug, service_id)
    return await slot_service.generate_slots(db, svc_id, payload)


@router.get("/tenants/{slug}/services/{service_id}/slots", response_model=list[SlotRead])
async def list_slots(
    slug: str,
    service_id: int,
    date: str | None = Query(default=None, description="Filter by date (YYYY-MM-DD)"),
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> list[SlotRead]:
    """List available slots for a service.

    Args:
        slug: Tenant slug.
        service_id: Service primary key.
        date: Optional date filter in ``YYYY-MM-DD`` format.
        db: Injected database connection.

    Returns:
        List of slots that still have remaining capacity.
    """
    svc_id = await _resolve_service(db, slug, service_id)
    return await slot_service.get_available_slots(db, svc_id, date)
