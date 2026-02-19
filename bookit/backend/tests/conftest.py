"""Shared pytest fixtures for BookIt backend tests."""

import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from src.bookit.main import app

# ────────────────────────────────────────────────
# In-memory DB fixture
# ────────────────────────────────────────────────


@pytest.fixture
async def test_db():
    """Create an in-memory SQLite database with BookIt schema.

    Yields:
        An open ``aiosqlite.Connection`` with ``row_factory = aiosqlite.Row``.
    """
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        # Replicate init_db logic for in-memory DB
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name TEXT NOT NULL,
                duration_min INTEGER NOT NULL DEFAULT 60,
                capacity INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL REFERENCES services(id),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 1,
                booked_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_id INTEGER NOT NULL REFERENCES slots(id),
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.commit()
        yield db


# ────────────────────────────────────────────────
# HTTP client fixture with dependency override
# ────────────────────────────────────────────────


@pytest.fixture
async def test_client(test_db):
    """AsyncClient wired to the FastAPI app with the in-memory DB injected.

    The ``get_db`` dependency is overridden so all router calls use the
    shared in-memory SQLite connection from ``test_db``.

    Args:
        test_db: The in-memory database connection fixture.

    Yields:
        An ``httpx.AsyncClient`` configured for ASGI transport.
    """
    from src.bookit.routers.bookings import get_db_dep as bookings_dep
    from src.bookit.routers.services import get_db_dep as services_dep
    from src.bookit.routers.slots import get_db_dep as slots_dep
    from src.bookit.routers.tenants import get_db_dep as tenants_dep

    async def override_db():
        yield test_db

    app.dependency_overrides[tenants_dep] = override_db
    app.dependency_overrides[services_dep] = override_db
    app.dependency_overrides[slots_dep] = override_db
    app.dependency_overrides[bookings_dep] = override_db

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
    """Insert a sample tenant and return its row dict.

    Args:
        test_db: In-memory database connection.

    Returns:
        Dict with ``id``, ``name``, ``slug``, ``created_at``.
    """
    cursor = await test_db.execute(
        "INSERT INTO tenants (name, slug) VALUES (?, ?)",
        ("Test Salon", "test-salon"),
    )
    await test_db.commit()
    tenant_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    row = await cursor.fetchone()
    return dict(row)


@pytest.fixture
async def sample_service(test_db, sample_tenant):
    """Insert a sample service for ``sample_tenant`` and return its row dict.

    Args:
        test_db: In-memory database connection.
        sample_tenant: The parent tenant fixture.

    Returns:
        Dict with service fields.
    """
    cursor = await test_db.execute(
        "INSERT INTO services (tenant_id, name, duration_min, capacity) VALUES (?, ?, ?, ?)",
        (sample_tenant["id"], "Haircut", 60, 2),
    )
    await test_db.commit()
    service_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    row = await cursor.fetchone()
    return dict(row)


@pytest.fixture
async def sample_slot(test_db, sample_service):
    """Insert a sample slot for ``sample_service`` and return its row dict.

    The slot is set far in the future so cancellation deadline tests can rely
    on it being cancellable by default.

    Args:
        test_db: In-memory database connection.
        sample_service: The parent service fixture.

    Returns:
        Dict with slot fields.
    """
    cursor = await test_db.execute(
        """
        INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            sample_service["id"],
            "2099-06-01T09:00:00",
            "2099-06-01T10:00:00",
            2,
            0,
        ),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
    row = await cursor.fetchone()
    return dict(row)
