"""Inventory service with pessimistic locking via SELECT FOR UPDATE.

All stock mutations go through this service. reserve_stock() is the
critical path that prevents overselling.
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
    """Set stock for a variant. Creates inventory record if it doesn't exist."""
    result = await session.execute(
        select(InventoryRecord).where(InventoryRecord.variant_id == variant_id)
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

    Acquires a row-level lock on the inventory record, checks available
    quantity, creates a reservation, and updates reserved count atomically.

    Raises:
        ValueError: If variant has no inventory record or insufficient stock.
    """
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
    """Convert a reservation to a fulfilled order: deduct on_hand, release reserved."""
    res_result = await session.execute(
        select(InventoryReservation)
        .where(InventoryReservation.id == reservation_id)
        .with_for_update()
    )
    reservation = res_result.scalar_one_or_none()
    if reservation is None or reservation.status != "active":
        raise ValueError(f"Reservation {reservation_id} not found or not active")

    inv_result = await session.execute(
        select(InventoryRecord)
        .where(InventoryRecord.variant_id == reservation.variant_id)
        .with_for_update()
    )
    record = inv_result.scalar_one()

    record.quantity_on_hand -= reservation.quantity
    record.quantity_reserved -= reservation.quantity
    reservation.status = "fulfilled"

    await session.flush()


async def cancel_reservation(session: AsyncSession, reservation_id: int) -> None:
    """Cancel a reservation and release the reserved stock."""
    res_result = await session.execute(
        select(InventoryReservation)
        .where(InventoryReservation.id == reservation_id)
        .with_for_update()
    )
    reservation = res_result.scalar_one_or_none()
    if reservation is None or reservation.status != "active":
        raise ValueError(f"Reservation {reservation_id} not found or not active")

    inv_result = await session.execute(
        select(InventoryRecord)
        .where(InventoryRecord.variant_id == reservation.variant_id)
        .with_for_update()
    )
    record = inv_result.scalar_one()

    record.quantity_reserved -= reservation.quantity
    reservation.status = "cancelled"

    await session.flush()


async def expire_stale_reservations(session: AsyncSession) -> int:
    """Expire all reservations past their TTL. Returns count expired."""
    now = datetime.now(UTC)
    result = await session.execute(
        select(InventoryReservation)
        .where(
            InventoryReservation.status == "active",
            InventoryReservation.expires_at < now,
        )
        .with_for_update()
    )
    expired_list = result.scalars().all()

    count = 0
    for reservation in expired_list:
        inv_result = await session.execute(
            select(InventoryRecord)
            .where(InventoryRecord.variant_id == reservation.variant_id)
            .with_for_update()
        )
        record = inv_result.scalar_one()
        record.quantity_reserved -= reservation.quantity
        reservation.status = "expired"
        count += 1

    await session.flush()
    return count
