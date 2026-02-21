"""Tests for reservation expiration logic."""

from datetime import UTC, datetime, timedelta

import pytest

from storeit.models.inventory import InventoryReservation


@pytest.mark.asyncio
async def test_expire_stale_reservations(test_session, sample_variant):
    """Expired reservations are released and stock becomes available again."""
    from storeit.services.inventory_service import (
        expire_stale_reservations,
        get_stock,
        reserve_stock,
    )

    # Reserve 5 items
    reservation = await reserve_stock(test_session, sample_variant.id, 5, "cart-expire")

    # Manually backdate the expiry to the past
    reservation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await test_session.flush()

    # Run expiration
    count = await expire_stale_reservations(test_session)
    assert count == 1

    # Verify stock is released
    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_on_hand == 50  # unchanged
    assert stock.quantity_reserved == 0  # released


@pytest.mark.asyncio
async def test_expire_does_not_touch_active_reservations(test_session, sample_variant):
    """Non-expired reservations remain active."""
    from storeit.services.inventory_service import (
        expire_stale_reservations,
        get_stock,
        reserve_stock,
    )

    # Reserve 3 items (TTL is 15 min in the future by default)
    await reserve_stock(test_session, sample_variant.id, 3, "cart-active")

    # Run expiration — nothing should expire
    count = await expire_stale_reservations(test_session)
    assert count == 0

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_reserved == 3  # still reserved


@pytest.mark.asyncio
async def test_expire_is_idempotent(test_session, sample_variant):
    """Running expiration twice doesn't double-release stock."""
    from storeit.services.inventory_service import (
        expire_stale_reservations,
        get_stock,
        reserve_stock,
    )

    reservation = await reserve_stock(test_session, sample_variant.id, 5, "cart-idem")
    reservation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await test_session.flush()

    count1 = await expire_stale_reservations(test_session)
    assert count1 == 1

    count2 = await expire_stale_reservations(test_session)
    assert count2 == 0

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_reserved == 0


@pytest.mark.asyncio
async def test_expire_multiple_reservations(test_session, sample_variant):
    """Multiple expired reservations for different carts are all released."""
    from storeit.services.inventory_service import (
        expire_stale_reservations,
        get_stock,
        reserve_stock,
    )

    r1 = await reserve_stock(test_session, sample_variant.id, 3, "cart-1")
    r2 = await reserve_stock(test_session, sample_variant.id, 7, "cart-2")

    r1.expires_at = datetime.now(UTC) - timedelta(minutes=5)
    r2.expires_at = datetime.now(UTC) - timedelta(minutes=2)
    await test_session.flush()

    count = await expire_stale_reservations(test_session)
    assert count == 2

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_reserved == 0
    assert stock.quantity_on_hand == 50  # no deduction, just released


@pytest.mark.asyncio
async def test_reservation_status_after_expiry(test_session, sample_variant):
    """Expired reservation has status='expired'."""
    from sqlalchemy import select

    from storeit.services.inventory_service import expire_stale_reservations, reserve_stock

    reservation = await reserve_stock(test_session, sample_variant.id, 1, "cart-status")
    reservation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await test_session.flush()

    await expire_stale_reservations(test_session)

    result = await test_session.execute(
        select(InventoryReservation).where(InventoryReservation.id == reservation.id)
    )
    updated = result.scalar_one()
    assert updated.status == "expired"
