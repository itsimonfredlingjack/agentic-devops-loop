"""Bookings router — create, cancel, and list customer bookings."""

import aiosqlite
from fastapi import APIRouter, Depends, Query

from src.bookit.database import get_db
from src.bookit.schemas.booking import BookingCreate, BookingRead
from src.bookit.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


@router.post("", response_model=BookingRead, status_code=201)
async def create_booking(
    payload: BookingCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> BookingRead:
    """Create a new booking.

    Args:
        payload: Booking creation payload.
        db: Injected database connection.

    Returns:
        The newly created booking.

    Raises:
        HTTPException 404: If the slot does not exist.
        HTTPException 409: If no capacity remains or the email is already
            booked for this slot.
    """
    return await booking_service.create_booking(db, payload)


@router.delete("/{booking_id}", response_model=BookingRead)
async def cancel_booking(
    booking_id: int,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> BookingRead:
    """Cancel a confirmed booking.

    Args:
        booking_id: Primary key of the booking to cancel.
        db: Injected database connection.

    Returns:
        The updated booking with ``status='cancelled'``.

    Raises:
        HTTPException 404: If the booking does not exist.
        HTTPException 400: If already cancelled or past the cancellation
            deadline.
    """
    return await booking_service.cancel_booking(db, booking_id)


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    email: str = Query(..., description="Customer email address"),
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> list[BookingRead]:
    """List all bookings for a customer email.

    Args:
        email: Customer email address to filter by.
        db: Injected database connection.

    Returns:
        List of bookings, most recent first.
    """
    return await booking_service.list_bookings_by_email(db, email)
