"""Project service — CRUD operations."""

import aiosqlite

from trackit.schemas.project import ProjectCreate, ProjectRead
from trackit.services.tenant_service import get_tenant_by_slug


async def create_project(
    db: aiosqlite.Connection, tenant_slug: str, payload: ProjectCreate
) -> ProjectRead:
    """Create a project under a tenant. Raises ValueError if tenant not found."""
    tenant = await get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    cursor = await db.execute(
        "INSERT INTO projects (tenant_id, name, hourly_rate_cents) VALUES (?, ?, ?)",
        (tenant.id, payload.name, payload.hourly_rate_cents),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,))
    ).fetchone()
    return _row_to_project(row)


async def list_projects(db: aiosqlite.Connection, tenant_slug: str) -> list[ProjectRead]:
    """List all projects for a tenant. Raises ValueError if tenant not found."""
    tenant = await get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    rows = await (
        await db.execute(
            "SELECT * FROM projects WHERE tenant_id = ? ORDER BY created_at",
            (tenant.id,),
        )
    ).fetchall()
    return [_row_to_project(r) for r in rows]


async def get_project(db: aiosqlite.Connection, project_id: int) -> ProjectRead | None:
    """Fetch a single project by ID."""
    row = await (await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))).fetchone()
    if row is None:
        return None
    return _row_to_project(row)


def _row_to_project(row: aiosqlite.Row) -> ProjectRead:
    return ProjectRead(
        id=row["id"],
        tenant_id=row["tenant_id"],
        name=row["name"],
        hourly_rate_cents=row["hourly_rate_cents"],
        created_at=row["created_at"],
    )
