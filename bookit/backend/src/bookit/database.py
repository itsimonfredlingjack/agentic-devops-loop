"""Async SQLite database access via aiosqlite."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite

from src.bookit.config import settings

# DDL statements — executed once at startup
_CREATE_TENANTS = """
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_SERVICES = """
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    duration_min INTEGER NOT NULL DEFAULT 60,
    capacity INTEGER NOT NULL DEFAULT 1,
    price_cents INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_SLOTS = """
CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER NOT NULL REFERENCES services(id),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 1,
    booked_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_BOOKINGS = """
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL REFERENCES slots(id),
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    stripe_session_id TEXT,
    payment_status TEXT NOT NULL DEFAULT 'none',
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


async def init_db(db_url: str | None = None) -> None:
    """Create all tables if they do not already exist.

    Args:
        db_url: Optional override for the database path.  Defaults to
            ``settings.database_url``.
    """
    url = db_url or settings.database_url
    async with aiosqlite.connect(url) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(_CREATE_TENANTS)
        await db.execute(_CREATE_SERVICES)
        await db.execute(_CREATE_SLOTS)
        await db.execute(_CREATE_BOOKINGS)

        # Migrations for existing databases
        await _migrate_add_column(db, "bookings", "customer_phone", "TEXT")
        await _migrate_add_column(db, "services", "price_cents", "INTEGER DEFAULT 0")
        await _migrate_add_column(db, "bookings", "stripe_session_id", "TEXT")
        await _migrate_add_column(db, "bookings", "payment_status", "TEXT DEFAULT 'none'")

        await db.commit()


async def _migrate_add_column(
    db: aiosqlite.Connection, table: str, column: str, col_type: str
) -> None:
    """Add a column to a table if it does not already exist."""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in await cursor.fetchall()]
    if column not in cols:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


@asynccontextmanager
async def get_db(db_url: str | None = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager that yields an aiosqlite connection.

    The connection has ``row_factory = aiosqlite.Row`` so rows behave
    like dicts.

    Args:
        db_url: Optional override for the database path.

    Yields:
        An open ``aiosqlite.Connection``.
    """
    url = db_url or settings.database_url
    async with aiosqlite.connect(url) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
