"""Shared pytest fixtures for TrackIt backend tests."""

import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from trackit.database import _CREATE_PROJECTS, _CREATE_TENANTS, _CREATE_TIME_ENTRIES
from trackit.main import app

# ────────────────────────────────────────────────
# In-memory DB fixture
# ────────────────────────────────────────────────


@pytest.fixture
async def test_db():
    """Create an in-memory SQLite database with TrackIt schema.

    Yields:
        An open ``aiosqlite.Connection`` with ``row_factory = aiosqlite.Row``.
    """
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(_CREATE_TENANTS)
        await db.execute(_CREATE_PROJECTS)
        await db.execute(_CREATE_TIME_ENTRIES)
        await db.commit()
        yield db


# ────────────────────────────────────────────────
# HTTP client fixture with dependency override
# ────────────────────────────────────────────────


@pytest.fixture
async def test_client(test_db):
    """AsyncClient wired to the FastAPI app with the in-memory DB injected.

    The ``get_db_dep`` dependency is overridden so all router calls use the
    shared in-memory SQLite connection from ``test_db``.
    """
    from trackit.routers.invoice import get_db_dep as invoice_dep
    from trackit.routers.projects import get_db_dep as projects_dep
    from trackit.routers.tenants import get_db_dep as tenants_dep

    async def override_db():
        yield test_db

    app.dependency_overrides[tenants_dep] = override_db
    app.dependency_overrides[projects_dep] = override_db
    app.dependency_overrides[invoice_dep] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ────────────────────────────────────────────────
# Domain object fixtures
# ────────────────────────────────────────────────


@pytest.fixture
async def sample_tenant(test_db):
    """Insert a sample tenant and return its row dict."""
    cursor = await test_db.execute(
        "INSERT INTO tenants (slug, name) VALUES (?, ?)",
        ("acme-consulting", "Acme Consulting"),
    )
    await test_db.commit()
    tenant_id = cursor.lastrowid
    row = await (
        await test_db.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    ).fetchone()
    return dict(row)


@pytest.fixture
async def sample_project(test_db, sample_tenant):
    """Insert a sample project for ``sample_tenant`` and return its row dict."""
    cursor = await test_db.execute(
        "INSERT INTO projects (tenant_id, name, hourly_rate_cents) VALUES (?, ?, ?)",
        (sample_tenant["id"], "Backend Dev", 150000),
    )
    await test_db.commit()
    project_id = cursor.lastrowid
    row = await (
        await test_db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    ).fetchone()
    return dict(row)
