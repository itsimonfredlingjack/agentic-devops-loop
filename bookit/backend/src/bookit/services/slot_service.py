"""Slot business-logic: availability queries and bulk generation."""

from datetime import datetime, timedelta

import aiosqlite
from fastapi import HTTPException

from src.bookit.schemas.slot import SlotBulkCreate, SlotRead


def _row_to_slot(row: aiosqlite.Row) -> SlotRead:
    """Convert a raw DB row to a SlotRead schema.

    Args:
        row: An ``aiosqlite.Row`` from the ``slots`` table.

    Returns:
        A populated ``SlotRead`` instance.
    """
    return SlotRead(
        id=row["id"],
        service_id=row["service_id"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        capacity=row["capacity"],
        booked_count=row["booked_count"],
        created_at=row["created_at"],
    )


async def get_available_slots(
    db: aiosqlite.Connection,
    service_id: int,
    date_filter: str | None = None,
) -> list[SlotRead]:
    """Return slots for a service that still have remaining capacity.

    Args:
        db: Open database connection.
        service_id: Primary key of the service.
        date_filter: Optional ``YYYY-MM-DD`` string to restrict results to a
            single day.

    Returns:
        List of available ``SlotRead`` objects ordered by start_time.
    """
    if date_filter:
        cursor = await db.execute(
            """
            SELECT * FROM slots
            WHERE service_id = ?
              AND booked_count < capacity
              AND date(start_time) = date(?)
            ORDER BY start_time
            """,
            (service_id, date_filter),
        )
    else:
        cursor = await db.execute(
            """
            SELECT * FROM slots
            WHERE service_id = ?
              AND booked_count < capacity
            ORDER BY start_time
            """,
            (service_id,),
        )
    rows = await cursor.fetchall()
    return [_row_to_slot(r) for r in rows]


async def check_overlap(
    db: aiosqlite.Connection,
    service_id: int,
    start: datetime,
    end: datetime,
) -> bool:
    """Check whether a proposed slot overlaps any existing slot for the service.

    Two intervals overlap when ``start < existing_end AND end > existing_start``.

    Args:
        db: Open database connection.
        service_id: Primary key of the service.
        start: Proposed slot start (timezone-naive ISO 8601).
        end: Proposed slot end (timezone-naive ISO 8601).

    Returns:
        ``True`` if an overlap exists, ``False`` otherwise.
    """
    start_str = start.isoformat()
    end_str = end.isoformat()
    cursor = await db.execute(
        """
        SELECT COUNT(*) FROM slots
        WHERE service_id = ?
          AND start_time < ?
          AND end_time > ?
        """,
        (service_id, end_str, start_str),
    )
    row = await cursor.fetchone()
    return bool(row and row[0] > 0)


async def create_slot(
    db: aiosqlite.Connection,
    service_id: int,
    start: datetime,
    end: datetime,
    capacity: int = 1,
) -> SlotRead:
    """Insert a single slot, checking for overlaps first.

    Args:
        db: Open database connection.
        service_id: Primary key of the service.
        start: Slot start datetime.
        end: Slot end datetime.
        capacity: Maximum number of concurrent bookings.

    Returns:
        The newly created ``SlotRead``.

    Raises:
        HTTPException 409: If the slot overlaps an existing slot.
    """
    if await check_overlap(db, service_id, start, end):
        raise HTTPException(
            status_code=409,
            detail="Slot overlaps an existing slot for this service",
        )
    start_str = start.isoformat()
    end_str = end.isoformat()
    cursor = await db.execute(
        """
        INSERT INTO slots (service_id, start_time, end_time, capacity)
        VALUES (?, ?, ?, ?)
        """,
        (service_id, start_str, end_str, capacity),
    )
    await db.commit()
    slot_id = cursor.lastrowid
    cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
    row = await cursor.fetchone()
    return _row_to_slot(row)


async def generate_slots(
    db: aiosqlite.Connection,
    service_id: int,
    bulk: SlotBulkCreate,
) -> list[SlotRead]:
    """Generate a series of equally spaced slots for a given day.

    Slots are generated from ``start_hour`` to ``end_hour`` with
    ``interval_min`` gaps.  Slots that overlap existing records are
    silently skipped rather than causing an error.

    Args:
        db: Open database connection.
        service_id: Primary key of the service.
        bulk: Parameters describing the generation schedule.

    Returns:
        List of created ``SlotRead`` objects.
    """
    created: list[SlotRead] = []
    current = datetime(bulk.date.year, bulk.date.month, bulk.date.day, bulk.start_hour, 0, 0)
    end_boundary = datetime(bulk.date.year, bulk.date.month, bulk.date.day, bulk.end_hour, 0, 0)
    delta = timedelta(minutes=bulk.interval_min)

    while current + delta <= end_boundary:
        slot_end = current + delta
        if not await check_overlap(db, service_id, current, slot_end):
            start_str = current.isoformat()
            end_str = slot_end.isoformat()
            cursor = await db.execute(
                """
                INSERT INTO slots (service_id, start_time, end_time, capacity)
                VALUES (?, ?, ?, ?)
                """,
                (service_id, start_str, end_str, bulk.capacity),
            )
            await db.commit()
            slot_id = cursor.lastrowid
            cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
            row = await cursor.fetchone()
            created.append(_row_to_slot(row))
        current += delta

    return created
