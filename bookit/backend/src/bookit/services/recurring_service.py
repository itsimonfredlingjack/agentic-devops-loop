"""Recurring booking logic — create and cancel series of bookings."""

import logging
from datetime import datetime, timedelta

import aiosqlite
from fastapi import HTTPException

from src.bookit.schemas.recurring import RecurringCreate, RecurringFrequency, RecurringRead

logger = logging.getLogger(__name__)

_FREQ_DAYS = {
    RecurringFrequency.weekly: 7,
    RecurringFrequency.biweekly: 14,
    RecurringFrequency.monthly: 30,
}


async def create_recurring_booking(
    db: aiosqlite.Connection,
    data: RecurringCreate,
) -> RecurringRead:
    """Create a series of recurring bookings.

    Finds or creates future slots with matching time offset, books each one.

    Args:
        db: Open database connection.
        data: Validated recurring booking payload.

    Returns:
        A ``RecurringRead`` with the rule and list of booking IDs.

    Raises:
        HTTPException 404: If the base slot does not exist.
        HTTPException 409: If any slot lacks capacity.
    """
    # Fetch original slot
    cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (data.slot_id,))
    base_slot = await cursor.fetchone()
    if base_slot is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    # Parse times
    start_dt = datetime.fromisoformat(base_slot["start_time"])
    end_dt = datetime.fromisoformat(base_slot["end_time"])
    delta = timedelta(days=_FREQ_DAYS[data.frequency])

    # Create recurring rule
    cursor = await db.execute(
        "INSERT INTO recurring_rules (frequency, occurrences) VALUES (?, ?)",
        (data.frequency, data.occurrences),
    )
    rule_id = cursor.lastrowid

    booking_ids: list[int] = []

    for i in range(data.occurrences):
        target_start = start_dt + delta * i
        target_end = end_dt + delta * i
        target_start_str = target_start.isoformat()
        target_end_str = target_end.isoformat()

        # Find existing slot or create one
        cursor = await db.execute(
            "SELECT * FROM slots WHERE service_id = ? AND start_time = ?",
            (base_slot["service_id"], target_start_str),
        )
        slot_row = await cursor.fetchone()

        if slot_row is None:
            # Create a new slot with same capacity as base
            cursor = await db.execute(
                "INSERT INTO slots (service_id, start_time, end_time, capacity) "
                "VALUES (?, ?, ?, ?)",
                (
                    base_slot["service_id"],
                    target_start_str,
                    target_end_str,
                    base_slot["capacity"],
                ),
            )
            slot_id = cursor.lastrowid
            cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
            slot_row = await cursor.fetchone()

        # Check capacity
        if slot_row["booked_count"] >= slot_row["capacity"]:
            raise HTTPException(
                status_code=409,
                detail=f"No capacity for slot at {target_start_str}",
            )

        # Create booking
        cursor = await db.execute(
            "INSERT INTO bookings "
            "(slot_id, customer_name, customer_email, customer_phone, "
            "recurring_rule_id) VALUES (?, ?, ?, ?, ?)",
            (
                slot_row["id"],
                data.customer_name,
                data.customer_email,
                data.customer_phone,
                rule_id,
            ),
        )
        booking_ids.append(cursor.lastrowid)

        # Increment booked_count
        await db.execute(
            "UPDATE slots SET booked_count = booked_count + 1 WHERE id = ?",
            (slot_row["id"],),
        )

    await db.commit()

    cursor = await db.execute("SELECT * FROM recurring_rules WHERE id = ?", (rule_id,))
    rule_row = await cursor.fetchone()

    return RecurringRead(
        id=rule_row["id"],
        frequency=RecurringFrequency(rule_row["frequency"]),
        occurrences=rule_row["occurrences"],
        booking_ids=booking_ids,
        created_at=rule_row["created_at"],
    )


async def get_recurring_rule(db: aiosqlite.Connection, rule_id: int) -> RecurringRead:
    """Fetch a recurring rule and its associated bookings."""
    cursor = await db.execute("SELECT * FROM recurring_rules WHERE id = ?", (rule_id,))
    rule = await cursor.fetchone()
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurring rule not found")

    cursor = await db.execute(
        "SELECT id FROM bookings WHERE recurring_rule_id = ? ORDER BY id",
        (rule_id,),
    )
    rows = await cursor.fetchall()

    return RecurringRead(
        id=rule["id"],
        frequency=RecurringFrequency(rule["frequency"]),
        occurrences=rule["occurrences"],
        booking_ids=[r["id"] for r in rows],
        created_at=rule["created_at"],
    )


async def cancel_recurring_series(db: aiosqlite.Connection, rule_id: int) -> int:
    """Cancel all future confirmed bookings in a series.

    Returns:
        Number of bookings cancelled.
    """
    cursor = await db.execute("SELECT * FROM recurring_rules WHERE id = ?", (rule_id,))
    rule = await cursor.fetchone()
    if rule is None:
        raise HTTPException(status_code=404, detail="Recurring rule not found")

    # Get all confirmed bookings for this rule
    cursor = await db.execute(
        "SELECT b.id, b.slot_id FROM bookings b "
        "WHERE b.recurring_rule_id = ? AND b.status = 'confirmed'",
        (rule_id,),
    )
    rows = await cursor.fetchall()

    count = 0
    for row in rows:
        await db.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (row["id"],),
        )
        await db.execute(
            "UPDATE slots SET booked_count = MAX(0, booked_count - 1) WHERE id = ?",
            (row["slot_id"],),
        )
        count += 1

    await db.commit()
    return count
