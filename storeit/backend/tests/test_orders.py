"""Order API tests -- lifecycle and state machine."""

import pytest

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────


async def _setup_cart_with_item(test_client, variant_id, session_id="order-session"):
    """Add an item to a cart and return the session_id."""
    await test_client.post(
        f"/api/cart/{session_id}/items",
        json={"variant_id": variant_id, "quantity": 2},
    )
    return session_id


# ────────────────────────────────────────────────
# Order creation
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_order(test_client, sample_variant):
    """POST /api/orders creates an order from a cart."""
    sid = await _setup_cart_with_item(test_client, sample_variant.id)

    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "test@example.com",
            "customer_name": "Test User",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert data["customer_email"] == "test@example.com"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["total_cents"] == sample_variant.price_cents * 2


@pytest.mark.asyncio
async def test_create_order_empty_cart(test_client):
    """POST /api/orders with empty cart returns 400."""
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": "empty-session",
            "customer_email": "a@b.com",
            "customer_name": "No Cart",
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(test_client, sample_variant):
    """Order for more than available stock returns 409."""
    # Add 999 items (stock is 50)
    await test_client.post(
        "/api/cart/big-order/items",
        json={"variant_id": sample_variant.id, "quantity": 999},
    )
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": "big-order",
            "customer_email": "a@b.com",
            "customer_name": "Big Buyer",
        },
    )
    assert r.status_code == 409


# ────────────────────────────────────────────────
# Order retrieval
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_order(test_client, sample_variant):
    sid = await _setup_cart_with_item(test_client, sample_variant.id, "get-order-sess")
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "get@test.com",
            "customer_name": "Get Test",
        },
    )
    order_id = r.json()["id"]

    r = await test_client.get(f"/api/orders/{order_id}")
    assert r.status_code == 200
    assert r.json()["id"] == order_id


@pytest.mark.asyncio
async def test_get_order_not_found(test_client):
    r = await test_client.get("/api/orders/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_orders_by_email(test_client, sample_variant):
    sid = await _setup_cart_with_item(test_client, sample_variant.id, "list-order-sess")
    await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "list@test.com",
            "customer_name": "List Test",
        },
    )

    r = await test_client.get("/api/orders", params={"email": "list@test.com"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["customer_email"] == "list@test.com"


# ────────────────────────────────────────────────
# State machine
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_order_state_transitions(test_client, sample_variant):
    """Test full order lifecycle: pending -> paid -> processing -> shipped -> delivered."""
    sid = await _setup_cart_with_item(test_client, sample_variant.id, "lifecycle-sess")
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "life@test.com",
            "customer_name": "Lifecycle",
        },
    )
    oid = r.json()["id"]

    for status in ["paid", "processing", "shipped", "delivered"]:
        r = await test_client.patch(f"/api/orders/{oid}/status", json={"status": status})
        assert r.status_code == 200
        assert r.json()["status"] == status


@pytest.mark.asyncio
async def test_invalid_state_transition(test_client, sample_variant):
    """pending -> shipped is not allowed."""
    sid = await _setup_cart_with_item(test_client, sample_variant.id, "invalid-sess")
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "invalid@test.com",
            "customer_name": "Invalid",
        },
    )
    oid = r.json()["id"]

    r = await test_client.patch(f"/api/orders/{oid}/status", json={"status": "shipped"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_cancel_pending_order(test_client, sample_variant):
    """Cancelling a pending order releases reserved stock."""
    sid = await _setup_cart_with_item(test_client, sample_variant.id, "cancel-sess")
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": sid,
            "customer_email": "cancel@test.com",
            "customer_name": "Cancel",
        },
    )
    oid = r.json()["id"]

    # Stock should be reserved
    r = await test_client.get(f"/api/inventory/{sample_variant.id}")
    assert r.json()["quantity_reserved"] > 0

    # Cancel
    r = await test_client.patch(f"/api/orders/{oid}/status", json={"status": "cancelled"})
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    # Stock should be released
    r = await test_client.get(f"/api/inventory/{sample_variant.id}")
    assert r.json()["quantity_reserved"] == 0
