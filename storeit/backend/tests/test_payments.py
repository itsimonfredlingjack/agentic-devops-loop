"""Payment tests with mocked Stripe."""

import json
from unittest.mock import MagicMock, patch

import pytest

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────


async def _create_order_with_items(test_client, variant_id, session_id="pay-session"):
    """Create a cart with items and convert to an order. Returns order dict."""
    await test_client.post(
        f"/api/cart/{session_id}/items",
        json={"variant_id": variant_id, "quantity": 2},
    )
    r = await test_client.post(
        "/api/orders",
        json={
            "cart_session_id": session_id,
            "customer_email": "buyer@example.com",
            "customer_name": "Test Buyer",
        },
    )
    assert r.status_code == 201
    return r.json()


def _mock_stripe_session(session_id="cs_test_123", url="https://checkout.stripe.com/test"):
    """Create a mock Stripe Checkout Session object."""
    mock = MagicMock()
    mock.id = session_id
    mock.url = url
    return mock


def _make_webhook_event(event_type, session_id):
    """Build a Stripe webhook event dict."""
    return {
        "id": "evt_test_123",
        "type": event_type,
        "data": {
            "object": {
                "id": session_id,
                "payment_status": "paid",
            }
        },
    }


# ────────────────────────────────────────────────
# Checkout endpoint
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_checkout_disabled(test_client, sample_variant):
    """POST /api/payments/checkout returns 503 when Stripe is disabled."""
    order = await _create_order_with_items(test_client, sample_variant.id, "disabled-sess")
    r = await test_client.post("/api/payments/checkout", json={"order_id": order["id"]})
    assert r.status_code == 503
    assert "not enabled" in r.json()["detail"]


@pytest.mark.asyncio
@patch("storeit.routers.payments.settings")
@patch("storeit.services.payment_service.create_checkout_session")
async def test_checkout_creates_session(mock_create, mock_settings, test_client, sample_variant):
    """POST /api/payments/checkout creates a Stripe session and returns URL."""
    mock_settings.stripe_enabled = True
    mock_create.return_value = _mock_stripe_session("cs_abc", "https://stripe.com/pay")

    order = await _create_order_with_items(test_client, sample_variant.id, "checkout-sess")
    r = await test_client.post("/api/payments/checkout", json={"order_id": order["id"]})
    assert r.status_code == 201
    data = r.json()
    assert data["checkout_session_id"] == "cs_abc"
    assert data["checkout_url"] == "https://stripe.com/pay"

    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args
    assert call_kwargs.kwargs["order_id"] == order["id"]
    assert call_kwargs.kwargs["customer_email"] == "buyer@example.com"


@pytest.mark.asyncio
async def test_checkout_order_not_found(test_client):
    """POST /api/payments/checkout with invalid order returns 404."""
    with patch("storeit.routers.payments.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        r = await test_client.post("/api/payments/checkout", json={"order_id": 9999})
    assert r.status_code == 404


@pytest.mark.asyncio
@patch("storeit.routers.payments.settings")
@patch("storeit.services.payment_service.create_checkout_session")
async def test_checkout_non_pending_order(mock_create, mock_settings, test_client, sample_variant):
    """POST /api/payments/checkout rejects non-pending orders."""
    mock_settings.stripe_enabled = True
    mock_create.return_value = _mock_stripe_session()

    order = await _create_order_with_items(test_client, sample_variant.id, "non-pending")

    # First checkout succeeds
    await test_client.post("/api/payments/checkout", json={"order_id": order["id"]})

    # Transition to paid
    await test_client.patch(f"/api/orders/{order['id']}/status", json={"status": "paid"})

    # Second checkout should fail
    r = await test_client.post("/api/payments/checkout", json={"order_id": order["id"]})
    assert r.status_code == 400
    assert "pending" in r.json()["detail"]


# ────────────────────────────────────────────────
# Webhook endpoint
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_missing_signature(test_client):
    """POST /api/payments/webhook without Stripe-Signature returns 400."""
    r = await test_client.post(
        "/api/payments/webhook",
        content=b"{}",
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 400
    assert "Missing" in r.json()["detail"]


@pytest.mark.asyncio
@patch("storeit.services.payment_service.verify_webhook_signature")
async def test_webhook_invalid_signature(mock_verify, test_client):
    """POST /api/payments/webhook with bad signature returns 400."""
    mock_verify.side_effect = Exception("Invalid signature")

    r = await test_client.post(
        "/api/payments/webhook",
        content=b"{}",
        headers={
            "content-type": "application/json",
            "stripe-signature": "bad_sig",
        },
    )
    assert r.status_code == 400
    assert "Invalid signature" in r.json()["detail"]


@pytest.mark.asyncio
@patch("storeit.routers.payments.settings")
@patch("storeit.services.payment_service.verify_webhook_signature")
@patch("storeit.services.payment_service.create_checkout_session")
async def test_webhook_fulfills_order(
    mock_create, mock_verify, mock_settings, test_client, sample_variant
):
    """Webhook with checkout.session.completed transitions order to paid."""
    mock_settings.stripe_enabled = True
    stripe_session_id = "cs_fulfill_test"
    mock_create.return_value = _mock_stripe_session(stripe_session_id)

    # Create order and checkout
    order = await _create_order_with_items(test_client, sample_variant.id, "fulfill-sess")
    await test_client.post("/api/payments/checkout", json={"order_id": order["id"]})

    # Simulate webhook
    event = _make_webhook_event("checkout.session.completed", stripe_session_id)
    mock_verify.return_value = event

    r = await test_client.post(
        "/api/payments/webhook",
        content=json.dumps(event).encode(),
        headers={
            "content-type": "application/json",
            "stripe-signature": "valid_sig",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"received": True}

    # Verify order is now paid
    r = await test_client.get(f"/api/orders/{order['id']}")
    assert r.json()["status"] == "paid"


@pytest.mark.asyncio
@patch("storeit.services.payment_service.verify_webhook_signature")
async def test_webhook_idempotent(mock_verify, test_client, sample_variant, test_session):
    """Sending the same webhook twice doesn't fail or double-transition."""
    from storeit.models.order import Order, OrderStatus

    # Create a paid order directly
    order = Order(
        customer_email="idem@test.com",
        customer_name="Idempotent",
        status=OrderStatus.paid,
        total_cents=10000,
        stripe_session_id="cs_idem_123",
    )
    test_session.add(order)
    await test_session.flush()

    event = _make_webhook_event("checkout.session.completed", "cs_idem_123")
    mock_verify.return_value = event

    r = await test_client.post(
        "/api/payments/webhook",
        content=json.dumps(event).encode(),
        headers={
            "content-type": "application/json",
            "stripe-signature": "valid_sig",
        },
    )
    assert r.status_code == 200

    # Order still paid (not double-transitioned)
    r = await test_client.get(f"/api/orders/{order.id}")
    assert r.json()["status"] == "paid"


@pytest.mark.asyncio
@patch("storeit.services.payment_service.verify_webhook_signature")
async def test_webhook_ignores_other_events(mock_verify, test_client):
    """Non-checkout.session.completed events are acknowledged but ignored."""
    event = {
        "id": "evt_other",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_123"}},
    }
    mock_verify.return_value = event

    r = await test_client.post(
        "/api/payments/webhook",
        content=json.dumps(event).encode(),
        headers={
            "content-type": "application/json",
            "stripe-signature": "valid_sig",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"received": True}
