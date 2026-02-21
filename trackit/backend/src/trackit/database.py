"""Database setup and schema for TrackIt."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite

from trackit.config import settings

_CREATE_TENANTS = """
CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_PROJECTS = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    hourly_rate_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

_CREATE_TIME_ENTRIES = """
CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    date TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    is_billable INTEGER NOT NULL DEFAULT 1,
    is_invoiced INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


async def init_db(db_url: str | None = None) -> None:
    """Create all tables if they don't exist."""
    url = db_url or settings.database_url
    async with aiosqlite.connect(url) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(_CREATE_TENANTS)
        await db.execute(_CREATE_PROJECTS)
        await db.execute(_CREATE_TIME_ENTRIES)
        await db.commit()


@asynccontextmanager
async def get_db(db_url: str | None = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Per-request database connection."""
    url = db_url or settings.database_url
    async with aiosqlite.connect(url) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
