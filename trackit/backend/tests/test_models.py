"""Tests for database models and service layer CRUD operations."""

import pytest

# ────────────────────────────────────────────────
# Schema (table creation)
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tables_exist(test_db):
    """All three tables are created in the in-memory DB."""
    rows = await (
        await test_db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    ).fetchall()
    names = {r["name"] for r in rows}
    assert "tenants" in names
    assert "projects" in names
    assert "time_entries" in names


@pytest.mark.asyncio
async def test_foreign_keys_enabled(test_db):
    """PRAGMA foreign_keys is ON."""
    row = await (await test_db.execute("PRAGMA foreign_keys")).fetchone()
    assert row[0] == 1


@pytest.mark.asyncio
async def test_time_entry_duration_check(test_db, sample_project):
    """duration_minutes CHECK(duration_minutes > 0) prevents zero or negative."""
    import aiosqlite

    with pytest.raises(aiosqlite.IntegrityError):
        await test_db.execute(
            "INSERT INTO time_entries (project_id, date, duration_minutes) VALUES (?, ?, ?)",
            (sample_project["id"], "2025-01-15", 0),
        )


# ────────────────────────────────────────────────
# Tenant service
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_tenant_service(test_db):
    """tenant_service.create_tenant inserts a row and returns TenantRead."""
    from trackit.schemas.tenant import TenantCreate
    from trackit.services.tenant_service import create_tenant

    result = await create_tenant(test_db, TenantCreate(slug="test-co", name="Test Co"))
    assert result.id is not None
    assert result.slug == "test-co"
    assert result.name == "Test Co"
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_get_tenant_by_slug_found(test_db, sample_tenant):
    """get_tenant_by_slug returns a tenant when slug exists."""
    from trackit.services.tenant_service import get_tenant_by_slug

    result = await get_tenant_by_slug(test_db, "acme-consulting")
    assert result is not None
    assert result.slug == "acme-consulting"
    assert result.name == "Acme Consulting"


@pytest.mark.asyncio
async def test_get_tenant_by_slug_not_found(test_db):
    """get_tenant_by_slug returns None for unknown slug."""
    from trackit.services.tenant_service import get_tenant_by_slug

    result = await get_tenant_by_slug(test_db, "does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_duplicate_tenant_slug(test_db):
    """Inserting duplicate slug raises IntegrityError (UNIQUE constraint)."""
    import aiosqlite

    await test_db.execute("INSERT INTO tenants (slug, name) VALUES (?, ?)", ("dupe", "Dupe 1"))
    await test_db.commit()

    with pytest.raises(aiosqlite.IntegrityError):
        await test_db.execute("INSERT INTO tenants (slug, name) VALUES (?, ?)", ("dupe", "Dupe 2"))


# ────────────────────────────────────────────────
# Project service
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_project_service(test_db, sample_tenant):
    """project_service.create_project inserts a project under a tenant."""
    from trackit.schemas.project import ProjectCreate
    from trackit.services.project_service import create_project

    result = await create_project(
        test_db,
        "acme-consulting",
        ProjectCreate(name="Frontend", hourly_rate_cents=120000),
    )
    assert result.name == "Frontend"
    assert result.hourly_rate_cents == 120000
    assert result.tenant_id == sample_tenant["id"]


@pytest.mark.asyncio
async def test_create_project_tenant_not_found(test_db):
    """create_project raises ValueError when tenant does not exist."""
    from trackit.schemas.project import ProjectCreate
    from trackit.services.project_service import create_project

    with pytest.raises(ValueError, match="not found"):
        await create_project(
            test_db,
            "ghost-tenant",
            ProjectCreate(name="X", hourly_rate_cents=10000),
        )


@pytest.mark.asyncio
async def test_list_projects_service(test_db, sample_tenant):
    """list_projects returns all projects for a tenant."""
    from trackit.schemas.project import ProjectCreate
    from trackit.services.project_service import create_project, list_projects

    await create_project(
        test_db,
        "acme-consulting",
        ProjectCreate(name="P1", hourly_rate_cents=100000),
    )
    await create_project(
        test_db,
        "acme-consulting",
        ProjectCreate(name="P2", hourly_rate_cents=200000),
    )
    result = await list_projects(test_db, "acme-consulting")
    assert len(result) == 2
    names = {p.name for p in result}
    assert names == {"P1", "P2"}


# ────────────────────────────────────────────────
# Time entry service
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_time_service(test_db, sample_project):
    """time_service.log_time inserts a time entry and returns TimeEntryRead."""
    from trackit.schemas.time_entry import TimeEntryCreate
    from trackit.services.time_service import log_time

    result = await log_time(
        test_db,
        sample_project["id"],
        TimeEntryCreate(date="2025-01-15", duration_minutes=120),
    )
    assert result.project_id == sample_project["id"]
    assert result.date == "2025-01-15"
    assert result.duration_minutes == 120
    assert result.is_billable is True
    assert result.is_invoiced is False


@pytest.mark.asyncio
async def test_log_time_non_billable(test_db, sample_project):
    """log_time with is_billable=False stores correctly."""
    from trackit.schemas.time_entry import TimeEntryCreate
    from trackit.services.time_service import log_time

    result = await log_time(
        test_db,
        sample_project["id"],
        TimeEntryCreate(date="2025-01-15", duration_minutes=30, is_billable=False),
    )
    assert result.is_billable is False


@pytest.mark.asyncio
async def test_log_time_project_not_found(test_db):
    """log_time raises ValueError when project does not exist."""
    from trackit.schemas.time_entry import TimeEntryCreate
    from trackit.services.time_service import log_time

    with pytest.raises(ValueError, match="not found"):
        await log_time(
            test_db,
            9999,
            TimeEntryCreate(date="2025-01-15", duration_minutes=60),
        )


@pytest.mark.asyncio
async def test_list_time_entries(test_db, sample_project):
    """list_time_entries returns all entries for a project ordered by date."""
    from trackit.schemas.time_entry import TimeEntryCreate
    from trackit.services.time_service import list_time_entries, log_time

    await log_time(
        test_db,
        sample_project["id"],
        TimeEntryCreate(date="2025-01-20", duration_minutes=60),
    )
    await log_time(
        test_db,
        sample_project["id"],
        TimeEntryCreate(date="2025-01-10", duration_minutes=90),
    )
    entries = await list_time_entries(test_db, sample_project["id"])
    assert len(entries) == 2
    assert entries[0].date == "2025-01-10"
    assert entries[1].date == "2025-01-20"
