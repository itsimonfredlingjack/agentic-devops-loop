"""Tenant service — CRUD operations."""

import aiosqlite

from trackit.schemas.tenant import TenantCreate, TenantRead


async def create_tenant(db: aiosqlite.Connection, payload: TenantCreate) -> TenantRead:
    """Create a new tenant."""
    cursor = await db.execute(
        "INSERT INTO tenants (slug, name) VALUES (?, ?)",
        (payload.slug, payload.name),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM tenants WHERE id = ?", (cursor.lastrowid,))
    ).fetchone()
    return _row_to_tenant(row)


async def get_tenant_by_slug(db: aiosqlite.Connection, slug: str) -> TenantRead | None:
    """Fetch a tenant by slug. Returns None if not found."""
    row = await (await db.execute("SELECT * FROM tenants WHERE slug = ?", (slug,))).fetchone()
    if row is None:
        return None
    return _row_to_tenant(row)


def _row_to_tenant(row: aiosqlite.Row) -> TenantRead:
    return TenantRead(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        created_at=row["created_at"],
    )
