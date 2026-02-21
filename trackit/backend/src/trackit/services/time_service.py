"""Time entry service — CRUD operations."""

import aiosqlite

from trackit.schemas.time_entry import TimeEntryCreate, TimeEntryRead
from trackit.services.project_service import get_project


async def log_time(
    db: aiosqlite.Connection, project_id: int, payload: TimeEntryCreate
) -> TimeEntryRead:
    """Log a time entry for a project. Raises ValueError if project not found."""
    project = await get_project(db, project_id)
    if project is None:
        raise ValueError(f"Project {project_id} not found")

    cursor = await db.execute(
        """INSERT INTO time_entries (project_id, date, duration_minutes, is_billable)
           VALUES (?, ?, ?, ?)""",
        (project_id, payload.date, payload.duration_minutes, int(payload.is_billable)),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM time_entries WHERE id = ?", (cursor.lastrowid,))
    ).fetchone()
    return _row_to_entry(row)


async def list_time_entries(db: aiosqlite.Connection, project_id: int) -> list[TimeEntryRead]:
    """List all time entries for a project."""
    rows = await (
        await db.execute(
            "SELECT * FROM time_entries WHERE project_id = ? ORDER BY date",
            (project_id,),
        )
    ).fetchall()
    return [_row_to_entry(r) for r in rows]


def _row_to_entry(row: aiosqlite.Row) -> TimeEntryRead:
    return TimeEntryRead(
        id=row["id"],
        project_id=row["project_id"],
        date=row["date"],
        duration_minutes=row["duration_minutes"],
        is_billable=bool(row["is_billable"]),
        is_invoiced=bool(row["is_invoiced"]),
        created_at=row["created_at"],
    )
