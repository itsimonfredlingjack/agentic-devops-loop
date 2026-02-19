"""Tenant router — create and retrieve tenants."""

import re

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from src.bookit.database import get_db
from src.bookit.schemas.tenant import TenantCreate, TenantRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _slugify(name: str) -> str:
    """Convert a tenant name to a URL-safe slug.

    Args:
        name: Raw tenant name.

    Returns:
        Lowercase, hyphen-separated slug.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


@router.post("", response_model=TenantRead, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> TenantRead:
    """Create a new tenant.

    The slug is auto-generated from the name and must be unique.

    Args:
        payload: Tenant creation payload.
        db: Injected database connection.

    Returns:
        The newly created tenant.

    Raises:
        HTTPException 409: If a tenant with the same slug already exists.
    """
    slug = _slugify(payload.name)
    try:
        cursor = await db.execute(
            "INSERT INTO tenants (name, slug) VALUES (?, ?)",
            (payload.name, slug),
        )
        await db.commit()
        tenant_id = cursor.lastrowid
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"A tenant with slug '{slug}' already exists",
        ) from exc

    cursor = await db.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    row = await cursor.fetchone()
    return TenantRead(**dict(row))


@router.get("/{slug}", response_model=TenantRead)
async def get_tenant(
    slug: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> TenantRead:
    """Retrieve a tenant by slug.

    Args:
        slug: URL-safe tenant identifier.
        db: Injected database connection.

    Returns:
        The tenant record.

    Raises:
        HTTPException 404: If no tenant with that slug exists.
    """
    cursor = await db.execute("SELECT * FROM tenants WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    return TenantRead(**dict(row))
