"""Tests for Stripe payment integration."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def _enable_stripe(monkeypatch):
    """Enable Stripe for tests."""
    monkeypatch.setattr("src.bookit.routers.payments.settings.stripe_enabled", True)
    monkeypatch.setattr(
        "src.bookit.services.payment_service.settings.stripe_secret_key", "sk_test_xxx"
    )
    monkeypatch.setattr(
        "src.bookit.services.payment_service.settings.stripe_webhook_secret", "whsec_xxx"
    )


@pytest.fixture
async def paid_service(test_db, sample_tenant):
    """Create a service with a price."""
    cursor = await test_db.execute(
        "INSERT INTO services (tenant_id, name, duration_min, capacity, price_cents)"
        " VALUES (?, ?, ?, ?, ?)",
        (sample_tenant["id"], "Premium Cut", 60, 2, 29900),
    )
    await test_db.commit()
    service_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
    return dict(await cursor.fetchone())


@pytest.fixture
async def paid_slot(test_db, paid_service):
    """Create a slot for the paid service."""
    cursor = await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count)"
        " VALUES (?, ?, ?, ?, ?)",
        (paid_service["id"], "2099-06-01T09:00:00", "2099-06-01T10:00:00", 2, 0),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
    return dict(await cursor.fetchone())


async def test_checkout_disabled_by_default(test_client, paid_slot, sample_tenant):
    """Checkout returns 400 when Stripe is disabled."""
    resp = await test_client.post(
        "/api/bookings/checkout",
        json={
            "slot_id": paid_slot["id"],
            "customer_name": "Anna",
            "customer_email": "anna@test.se",
            "tenant_slug": sample_tenant["slug"],
        },
    )
    assert resp.status_code == 400
    assert "not enabled" in resp.json()["detail"]


async def test_checkout_creates_session(_enable_stripe, test_client, paid_slot, sample_tenant):
    """Checkout creates a Stripe session and pending booking."""
    mock_session = MagicMock()
    mock_session.id = "cs_test_123"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"

    with patch(
        "src.bookit.services.payment_service.stripe.checkout.Session.create",
        return_value=mock_session,
    ):
        resp = await test_client.post(
            "/api/bookings/checkout",
            json={
                "slot_id": paid_slot["id"],
                "customer_name": "Anna",
                "customer_email": "anna@test.se",
                "tenant_slug": sample_tenant["slug"],
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "cs_test_123"
    assert data["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_123"
    assert data["booking_id"] > 0


async def test_free_service_rejects_checkout(
    _enable_stripe, test_client, sample_slot, sample_tenant
):
    """Free services should use regular booking, not checkout."""
    resp = await test_client.post(
        "/api/bookings/checkout",
        json={
            "slot_id": sample_slot["id"],
            "customer_name": "Anna",
            "customer_email": "anna@test.se",
            "tenant_slug": sample_tenant["slug"],
        },
    )
    assert resp.status_code == 400
    assert "free" in resp.json()["detail"].lower()


async def test_webhook_confirms_booking(_enable_stripe, test_client, test_db, paid_slot):
    """Stripe webhook 'checkout.session.completed' confirms the booking."""
    # Create a pending booking manually
    cursor = await test_db.execute(
        "INSERT INTO bookings "
        "(slot_id, customer_name, customer_email, status, payment_status, "
        "stripe_session_id) VALUES (?, ?, ?, 'pending', 'pending', ?)",
        (paid_slot["id"], "Erik", "erik@test.se", "cs_test_456"),
    )
    await test_db.commit()
    booking_id = cursor.lastrowid

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_456",
                "metadata": {"booking_id": str(booking_id)},
            }
        },
    }

    with patch(
        "src.bookit.routers.payments.verify_webhook_signature",
        return_value=event,
    ):
        resp = await test_client.post(
            "/api/webhooks/stripe",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=abc"},
        )
    assert resp.status_code == 200

    # Verify booking is now confirmed + paid
    cursor = await test_db.execute(
        "SELECT status, payment_status FROM bookings WHERE id = ?", (booking_id,)
    )
    row = await cursor.fetchone()
    assert row["status"] == "confirmed"
    assert row["payment_status"] == "paid"


async def test_checkout_status_endpoint(test_client, test_db, paid_slot):
    """GET checkout status returns booking info by session_id."""
    await test_db.execute(
        "INSERT INTO bookings "
        "(slot_id, customer_name, customer_email, status, payment_status, "
        "stripe_session_id) VALUES (?, ?, ?, 'pending', 'pending', ?)",
        (paid_slot["id"], "Lisa", "lisa@test.se", "cs_test_789"),
    )
    await test_db.commit()

    resp = await test_client.get("/api/bookings/checkout/cs_test_789/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_status"] == "pending"
    assert data["booking_status"] == "pending"
