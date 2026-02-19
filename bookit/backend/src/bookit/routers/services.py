"""Services router — manage bookable services under a tenant."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from src.bookit.database import get_db
from src.bookit.schemas.service import ServiceCreate, ServiceRead

router = APIRouter(tags=["services"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


async def _get_tenant_id(db: aiosqlite.Connection, slug: str) -> int:
    """Resolve a tenant slug to its primary key.

    Args:
        db: Open database connection.
        slug: Tenant slug.

    Returns:
        The tenant's primary key.

    Raises:
        HTTPException 404: If the tenant does not exist.
    """
    cursor = await db.execute("SELECT id FROM tenants WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    return row["id"]


@router.post("/tenants/{slug}/services", response_model=ServiceRead, status_code=201)
async def create_service(
    slug: str,
    payload: ServiceCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> ServiceRead:
    """Create a service for a tenant.

    Args:
        slug: Tenant slug.
        payload: Service creation payload.
        db: Injected database connection.

    Returns:
        The newly created service.
    """
    tenant_id = await _get_tenant_id(db, slug)
    cursor = await db.execute(
        "INSERT INTO services (tenant_id, name, duration_min, capacity) VALUES (?, ?, ?, ?)",
        (tenant_id, payload.name, payload.duration_min, payload.capacity),
    )
    await db.commit()
    service_id = cursor.lastrowid
    cursor = await db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    row = await cursor.fetchone()
    return ServiceRead(**dict(row))


@router.get("/tenants/{slug}/services", response_model=list[ServiceRead])
async def list_services(
    slug: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> list[ServiceRead]:
    """List all services for a tenant.

    Args:
        slug: Tenant slug.
        db: Injected database connection.

    Returns:
        List of services belonging to the tenant.
    """
    tenant_id = await _get_tenant_id(db, slug)
    cursor = await db.execute(
        "SELECT * FROM services WHERE tenant_id = ? ORDER BY name",
        (tenant_id,),
    )
    rows = await cursor.fetchall()
    return [ServiceRead(**dict(r)) for r in rows]
