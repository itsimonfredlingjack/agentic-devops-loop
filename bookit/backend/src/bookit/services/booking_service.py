"""Booking business-logic: creation and cancellation with atomic DB updates."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import aiosqlite
from fastapi import HTTPException

from src.bookit.config import settings
from src.bookit.schemas.booking import BookingCreate, BookingRead, BookingStatus
from src.bookit.services.notification_service import (
    send_booking_confirmation,
    send_cancellation_notification,
)

logger = logging.getLogger(__name__)


def _row_to_booking(row: aiosqlite.Row) -> BookingRead:
    """Convert a raw DB row to a BookingRead schema.

    Args:
        row: An ``aiosqlite.Row`` from the ``bookings`` table.

    Returns:
        A populated ``BookingRead`` instance.
    """
    return BookingRead(
        id=row["id"],
        slot_id=row["slot_id"],
        customer_name=row["customer_name"],
        customer_email=row["customer_email"],
        customer_phone=row["customer_phone"],
        stripe_session_id=row["stripe_session_id"],
        payment_status=row["payment_status"],
        status=BookingStatus(row["status"]),
        created_at=row["created_at"],
    )


async def _get_service_name(db: aiosqlite.Connection, slot_row: aiosqlite.Row) -> str:
    """Look up the service name for a slot."""
    cursor = await db.execute("SELECT name FROM services WHERE id = ?", (slot_row["service_id"],))
    svc = await cursor.fetchone()
    return svc["name"] if svc else "Okänd tjänst"


async def create_booking(db: aiosqlite.Connection, booking: BookingCreate) -> BookingRead:
    """Create a new booking after verifying capacity and uniqueness.

    Capacity check and insert are performed inside a single transaction to
    prevent races between concurrent requests.

    Args:
        db: Open database connection.
        booking: Validated booking payload.

    Returns:
        The newly created ``BookingRead``.

    Raises:
        HTTPException 404: If the slot does not exist.
        HTTPException 409: If the slot has no remaining capacity, or if the
            customer has already booked this slot.
    """
    # Fetch slot
    cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (booking.slot_id,))
    slot_row = await cursor.fetchone()
    if slot_row is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot_row["booked_count"] >= slot_row["capacity"]:
        raise HTTPException(status_code=409, detail="No remaining capacity for this slot")

    # Check for duplicate booking by same email
    cursor = await db.execute(
        """
        SELECT id FROM bookings
        WHERE slot_id = ? AND customer_email = ? AND status = 'confirmed'
        """,
        (booking.slot_id, booking.customer_email),
    )
    existing = await cursor.fetchone()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="This email address already has a confirmed booking for this slot",
        )

    # Atomically insert booking and increment booked_count
    cursor = await db.execute(
        """
        INSERT INTO bookings (slot_id, customer_name, customer_email, customer_phone)
        VALUES (?, ?, ?, ?)
        """,
        (booking.slot_id, booking.customer_name, booking.customer_email, booking.customer_phone),
    )
    booking_id = cursor.lastrowid
    await db.execute(
        "UPDATE slots SET booked_count = booked_count + 1 WHERE id = ?",
        (booking.slot_id,),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = await cursor.fetchone()
    result = _row_to_booking(row)

    # Fire-and-forget email notification
    service_name = await _get_service_name(db, slot_row)
    asyncio.create_task(
        send_booking_confirmation(
            customer_name=booking.customer_name,
            customer_email=booking.customer_email,
            service_name=service_name,
            slot_start=slot_row["start_time"],
            slot_end=slot_row["end_time"],
        )
    )

    return result


async def cancel_booking(db: aiosqlite.Connection, booking_id: int) -> BookingRead:
    """Cancel a confirmed booking if within the cancellation deadline.

    Args:
        db: Open database connection.
        booking_id: Primary key of the booking to cancel.

    Returns:
        The updated ``BookingRead`` with ``status='cancelled'``.

    Raises:
        HTTPException 404: If the booking does not exist.
        HTTPException 400: If the booking is already cancelled or the
            cancellation deadline has passed.
    """
    cursor = await db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking_row = await cursor.fetchone()
    if booking_row is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking_row["status"] != BookingStatus.confirmed:
        raise HTTPException(status_code=400, detail="Booking is already cancelled")

    # Fetch slot to check deadline
    cursor = await db.execute("SELECT * FROM slots WHERE id = ?", (booking_row["slot_id"],))
    slot_row = await cursor.fetchone()

    slot_start = datetime.fromisoformat(slot_row["start_time"])
    # Make naive datetime UTC-aware for comparison
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    deadline = slot_start - timedelta(hours=settings.cancellation_deadline_hours)
    if now > deadline:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cancellation deadline has passed "
                f"({settings.cancellation_deadline_hours}h before slot start)"
            ),
        )

    # Atomically cancel booking and decrement booked_count
    await db.execute(
        "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
        (booking_id,),
    )
    await db.execute(
        "UPDATE slots SET booked_count = MAX(0, booked_count - 1) WHERE id = ?",
        (slot_row["id"],),
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = await cursor.fetchone()
    result = _row_to_booking(row)

    # Fire-and-forget cancellation email
    service_name = await _get_service_name(db, slot_row)
    asyncio.create_task(
        send_cancellation_notification(
            customer_name=booking_row["customer_name"],
            customer_email=booking_row["customer_email"],
            service_name=service_name,
            slot_start=slot_row["start_time"],
        )
    )

    return result


async def list_bookings_by_email(
    db: aiosqlite.Connection,
    email: str,
) -> list[BookingRead]:
    """Return all bookings for a given customer email.

    Args:
        db: Open database connection.
        email: Customer email address to filter by.

    Returns:
        List of ``BookingRead`` objects, most recent first.
    """
    cursor = await db.execute(
        "SELECT * FROM bookings WHERE customer_email = ? ORDER BY created_at DESC",
        (email,),
    )
    rows = await cursor.fetchall()
    return [_row_to_booking(r) for r in rows]
