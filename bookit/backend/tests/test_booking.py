"""Unit tests for booking_service business logic."""

import pytest

from src.bookit.schemas.booking import BookingCreate
from src.bookit.services import booking_service

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────


async def _book(db, slot_id: int, email: str = "customer@example.com", name: str = "Jane"):
    """Helper: create a booking and return it."""
    return await booking_service.create_booking(
        db,
        BookingCreate(slot_id=slot_id, customer_name=name, customer_email=email),
    )


# ────────────────────────────────────────────────
# create_booking
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_booking_success(test_db, sample_slot):
    """Happy path — booking is created and booked_count increments."""
    booking = await _book(test_db, sample_slot["id"])
    assert booking.id is not None
    assert booking.status.value == "confirmed"
    assert booking.customer_email == "customer@example.com"

    # Verify booked_count was incremented
    cursor = await test_db.execute(
        "SELECT booked_count FROM slots WHERE id = ?", (sample_slot["id"],)
    )
    row = await cursor.fetchone()
    assert row["booked_count"] == 1


@pytest.mark.asyncio
async def test_create_booking_no_capacity(test_db, sample_service):
    """409 when slot is already at capacity."""
    from fastapi import HTTPException

    # Create a slot with capacity=1
    cursor = await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (sample_service["id"], "2099-07-01T10:00:00", "2099-07-01T11:00:00", 1, 0),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid

    # First booking fills the slot
    await _book(test_db, slot_id, email="first@example.com")

    # Second booking should fail with 409
    with pytest.raises(HTTPException) as exc_info:
        await _book(test_db, slot_id, email="second@example.com")

    assert exc_info.value.status_code == 409
    assert "capacity" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_booking_duplicate_email_same_slot(test_db, sample_slot):
    """409 when same email tries to book the same slot twice."""
    from fastapi import HTTPException

    await _book(test_db, sample_slot["id"], email="dup@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await _book(test_db, sample_slot["id"], email="dup@example.com")

    assert exc_info.value.status_code == 409
    assert "already" in exc_info.value.detail.lower()


# ────────────────────────────────────────────────
# cancel_booking
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_booking_success(test_db, sample_slot):
    """Happy path — booking is cancelled and booked_count decrements."""
    booking = await _book(test_db, sample_slot["id"])
    cancelled = await booking_service.cancel_booking(test_db, booking.id)

    assert cancelled.status.value == "cancelled"

    # booked_count should be back to 0
    cursor = await test_db.execute(
        "SELECT booked_count FROM slots WHERE id = ?", (sample_slot["id"],)
    )
    row = await cursor.fetchone()
    assert row["booked_count"] == 0


@pytest.mark.asyncio
async def test_cancel_booking_past_deadline(test_db, sample_service):
    """400 when the slot starts in less than 24 hours."""
    from fastapi import HTTPException

    # Slot starting very soon (in the past, but still a valid future test case)
    cursor = await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            sample_service["id"],
            "2020-01-01T10:00:00",  # far in the past → deadline already passed
            "2020-01-01T11:00:00",
            1,
            0,
        ),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid

    # Manually insert a confirmed booking (bypassing capacity check for this test)
    cursor = await test_db.execute(
        "INSERT INTO bookings (slot_id, customer_name, customer_email, status) VALUES (?, ?, ?, ?)",
        (slot_id, "Jane", "jane@example.com", "confirmed"),
    )
    await test_db.execute("UPDATE slots SET booked_count = 1 WHERE id = ?", (slot_id,))
    await test_db.commit()
    booking_id = cursor.lastrowid

    with pytest.raises(HTTPException) as exc_info:
        await booking_service.cancel_booking(test_db, booking_id)

    assert exc_info.value.status_code == 400
    assert "deadline" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_cancel_booking_not_found(test_db):
    """404 when booking_id does not exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await booking_service.cancel_booking(test_db, 99999)

    assert exc_info.value.status_code == 404


# ────────────────────────────────────────────────
# list_bookings_by_email
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_bookings_by_email(test_db, sample_slot, sample_service):
    """Booking list filtered by email returns only matching records."""
    # Create a second future slot
    cursor = await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity) VALUES (?, ?, ?, ?)",
        (sample_service["id"], "2099-08-01T09:00:00", "2099-08-01T10:00:00", 5),
    )
    await test_db.commit()
    slot2_id = cursor.lastrowid

    await _book(test_db, sample_slot["id"], email="target@example.com", name="Target")
    await _book(test_db, slot2_id, email="target@example.com", name="Target")
    await _book(test_db, sample_slot["id"], email="other@example.com", name="Other")

    results = await booking_service.list_bookings_by_email(test_db, "target@example.com")
    assert len(results) == 2
    assert all(b.customer_email == "target@example.com" for b in results)
