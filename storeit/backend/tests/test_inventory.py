"""Inventory and reservation tests."""

import pytest


@pytest.mark.asyncio
async def test_get_stock(test_client, sample_variant):
    """GET /api/inventory/{variant_id} returns stock info."""
    r = await test_client.get(f"/api/inventory/{sample_variant.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["variant_id"] == sample_variant.id
    assert data["quantity_on_hand"] == 50
    assert data["quantity_reserved"] == 0


@pytest.mark.asyncio
async def test_get_stock_not_found(test_client):
    r = await test_client.get("/api/inventory/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_set_stock(test_client, sample_variant):
    """PUT /api/inventory/{variant_id} updates stock."""
    r = await test_client.put(
        f"/api/inventory/{sample_variant.id}",
        json={"quantity_on_hand": 100},
    )
    assert r.status_code == 200
    assert r.json()["quantity_on_hand"] == 100


@pytest.mark.asyncio
async def test_set_stock_creates_if_missing(test_client):
    """PUT creates inventory record for a new variant."""
    # Create a product + variant first
    r = await test_client.post("/api/products", json={"name": "New", "slug": "new-stock"})
    pid = r.json()["id"]
    r = await test_client.post(
        f"/api/products/{pid}/variants",
        json={"sku": "NS-001", "name": "Default", "price_cents": 5000},
    )
    vid = r.json()["id"]

    r = await test_client.put(f"/api/inventory/{vid}", json={"quantity_on_hand": 25})
    assert r.status_code == 200
    assert r.json()["quantity_on_hand"] == 25


# ────────────────────────────────────────────────
# Service-level reservation tests
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reserve_stock_service(test_session, sample_variant):
    """reserve_stock locks and reserves inventory."""
    from storeit.services.inventory_service import get_stock, reserve_stock

    reservation = await reserve_stock(test_session, sample_variant.id, 5, "cart-1")
    assert reservation.quantity == 5
    assert reservation.status == "active"

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_reserved == 5


@pytest.mark.asyncio
async def test_reserve_stock_insufficient(test_session, sample_variant):
    """reserve_stock raises ValueError when stock is insufficient."""
    from storeit.services.inventory_service import reserve_stock

    with pytest.raises(ValueError, match="Insufficient stock"):
        await reserve_stock(test_session, sample_variant.id, 999, "cart-1")


@pytest.mark.asyncio
async def test_reserve_stock_no_inventory(test_session):
    """reserve_stock raises ValueError when no inventory record exists."""
    from storeit.services.inventory_service import reserve_stock

    with pytest.raises(ValueError, match="No inventory record"):
        await reserve_stock(test_session, 9999, 1, "cart-1")


@pytest.mark.asyncio
async def test_fulfill_reservation(test_session, sample_variant):
    """fulfill_reservation deducts on_hand and releases reserved."""
    from storeit.services.inventory_service import (
        fulfill_reservation,
        get_stock,
        reserve_stock,
    )

    reservation = await reserve_stock(test_session, sample_variant.id, 10, "cart-1")
    await fulfill_reservation(test_session, reservation.id)

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_on_hand == 40  # 50 - 10
    assert stock.quantity_reserved == 0


@pytest.mark.asyncio
async def test_cancel_reservation(test_session, sample_variant):
    """cancel_reservation releases reserved stock back to available."""
    from storeit.services.inventory_service import (
        cancel_reservation,
        get_stock,
        reserve_stock,
    )

    reservation = await reserve_stock(test_session, sample_variant.id, 5, "cart-1")
    await cancel_reservation(test_session, reservation.id)

    stock = await get_stock(test_session, sample_variant.id)
    assert stock.quantity_on_hand == 50  # unchanged
    assert stock.quantity_reserved == 0  # released
