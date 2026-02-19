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
        await db.commit()


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
