"""Inventory service with pessimistic locking via SELECT FOR UPDATE.

All stock mutations go through this service. reserve_stock() is the
critical path that prevents overselling.

LOCK ORDERING: Always acquire InventoryRecord lock FIRST, then
InventoryReservation. This prevents ABBA deadlocks across all functions.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.config import settings
from storeit.models.inventory import InventoryRecord, InventoryReservation
from storeit.schemas.inventory import StockRead


async def get_stock(session: AsyncSession, variant_id: int) -> StockRead | None:
    """Get current inventory for a variant (no lock)."""
    result = await session.execute(
        select(InventoryRecord).where(InventoryRecord.variant_id == variant_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return StockRead.model_validate(record)


async def set_stock(session: AsyncSession, variant_id: int, quantity_on_hand: int) -> StockRead:
    """Set stock for a variant. Uses FOR UPDATE to prevent TOCTOU race."""
    result = await session.execute(
        select(InventoryRecord).where(InventoryRecord.variant_id == variant_id).with_for_update()
    )
    record = result.scalar_one_or_none()

    if record is None:
        record = InventoryRecord(
            variant_id=variant_id,
            quantity_on_hand=quantity_on_hand,
            quantity_reserved=0,
        )
        session.add(record)
    else:
        record.quantity_on_hand = quantity_on_hand

    await session.flush()
    return StockRead.model_validate(record)


async def reserve_stock(
    session: AsyncSession,
    variant_id: int,
    quantity: int,
    cart_id: str,
) -> InventoryReservation:
    """Reserve stock with SELECT FOR UPDATE to prevent overselling.

    Lock order: InventoryRecord first (consistent with all other functions).
    """
    # Lock inventory FIRST
    result = await session.execute(
        select(InventoryRecord).where(InventoryRecord.variant_id == variant_id).with_for_update()
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise ValueError(f"No inventory record for variant {variant_id}")

    available = record.quantity_on_hand - record.quantity_reserved
    if available < quantity:
        raise ValueError(
            f"Insufficient stock for variant {variant_id}: "
            f"requested {quantity}, available {available}"
        )

    expires_at = datetime.now(UTC) + timedelta(minutes=settings.reservation_ttl_minutes)
    reservation = InventoryReservation(
        variant_id=variant_id,
        quantity=quantity,
        cart_id=cart_id,
        expires_at=expires_at,
        status="active",
    )
    session.add(reservation)

    record.quantity_reserved += quantity
    await session.flush()

    return reservation


async def fulfill_reservation(session: AsyncSession, reservation_id: int) -> None:
    """Convert a reservation to fulfilled: deduct on_hand, release reserved.

    Lock order: InventoryRecord first, then InventoryReservation.
    """
    # Peek at reservation without lock to get variant_id
    res_peek = await session.execute(
        select(InventoryReservation).where(InventoryReservation.id == reservation_id)
    )
    reservation = res_peek.scalar_one_or_none()
    if reservation is None or reservation.status != "active":
        raise ValueError(f"Reservation {reservation_id} not found or not active")

    # Lock inventory FIRST
    inv_result = await session.execute(
        select(InventoryRecord)
        .where(InventoryRecord.variant_id == reservation.variant_id)
        .with_for_update()
    )
    record = inv_result.scalar_one_or_none()
    if record is None:
        raise ValueError(f"No inventory record for variant {reservation.variant_id}")

    # Then lock reservation
    res_result = await session.execute(
        select(InventoryReservation)
        .where(InventoryReservation.id == reservation_id)
        .with_for_update()
    )
    reservation = res_result.scalar_one()

    record.quantity_on_hand -= reservation.quantity
    record.quantity_reserved -= reservation.quantity
    reservation.status = "fulfilled"

    await session.flush()


async def cancel_reservation(session: AsyncSession, reservation_id: int) -> None:
    """Cancel a reservation and release the reserved stock.

    Lock order: InventoryRecord first, then InventoryReservation.
    """
    # Peek at reservation without lock to get variant_id
    res_peek = await session.execute(
        select(InventoryReservation).where(InventoryReservation.id == reservation_id)
    )
    reservation = res_peek.scalar_one_or_none()
    if reservation is None or reservation.status != "active":
        raise ValueError(f"Reservation {reservation_id} not found or not active")

    # Lock inventory FIRST
    inv_result = await session.execute(
        select(InventoryRecord)
        .where(InventoryRecord.variant_id == reservation.variant_id)
        .with_for_update()
    )
    record = inv_result.scalar_one_or_none()
    if record is None:
        raise ValueError(f"No inventory record for variant {reservation.variant_id}")

    # Then lock reservation
    res_result = await session.execute(
        select(InventoryReservation)
        .where(InventoryReservation.id == reservation_id)
        .with_for_update()
    )
    reservation = res_result.scalar_one()

    record.quantity_reserved -= reservation.quantity
    reservation.status = "cancelled"

    await session.flush()


async def expire_stale_reservations(session: AsyncSession) -> int:
    """Expire all reservations past their TTL. Returns count expired.

    Lock order: InventoryRecord first, then InventoryReservation.
    Processes one reservation at a time to maintain consistent lock ordering.
    """
    now = datetime.now(UTC)

    # Find expired reservation IDs without locking
    result = await session.execute(
        select(InventoryReservation.id, InventoryReservation.variant_id)
        .where(
            InventoryReservation.status == "active",
            InventoryReservation.expires_at < now,
        )
        .order_by(InventoryReservation.variant_id)  # Group by variant for fewer lock switches
    )
    expired_ids = [(row.id, row.variant_id) for row in result.all()]

    count = 0
    for reservation_id, variant_id in expired_ids:
        # Lock inventory FIRST
        inv_result = await session.execute(
            select(InventoryRecord)
            .where(InventoryRecord.variant_id == variant_id)
            .with_for_update()
        )
        record = inv_result.scalar_one_or_none()
        if record is None:
            continue

        # Then lock reservation
        res_result = await session.execute(
            select(InventoryReservation)
            .where(
                InventoryReservation.id == reservation_id,
                InventoryReservation.status == "active",  # Re-check under lock
            )
            .with_for_update()
        )
        reservation = res_result.scalar_one_or_none()
        if reservation is None:
            continue  # Already expired/cancelled by another process

        record.quantity_reserved -= reservation.quantity
        reservation.status = "expired"
        count += 1

    await session.flush()
    return count
