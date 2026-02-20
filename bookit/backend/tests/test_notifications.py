"""Tests for the email notification service."""

from unittest.mock import AsyncMock, patch

import pytest

from src.bookit.services.notification_service import (
    send_booking_confirmation,
    send_cancellation_notification,
)


@pytest.fixture
def _enable_email(monkeypatch):
    """Enable email for notification-unit tests."""
    monkeypatch.setattr("src.bookit.services.notification_service.settings.email_enabled", True)


@pytest.fixture
def mock_send():
    """Mock the low-level _send_email helper."""
    with patch(
        "src.bookit.services.notification_service._send_email",
        new_callable=AsyncMock,
    ) as m:
        yield m


async def test_confirmation_email_sent(_enable_email, mock_send):
    """Confirmation email is dispatched when email_enabled=True."""
    await send_booking_confirmation(
        customer_name="Anna",
        customer_email="anna@test.se",
        service_name="Klippning",
        slot_start="2099-06-01T09:00:00",
        slot_end="2099-06-01T10:00:00",
    )
    mock_send.assert_awaited_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "anna@test.se"
    assert "Bokningsbekräftelse" in call_args[0][1]


async def test_cancellation_email_sent(_enable_email, mock_send):
    """Cancellation email is dispatched when email_enabled=True."""
    await send_cancellation_notification(
        customer_name="Anna",
        customer_email="anna@test.se",
        service_name="Klippning",
        slot_start="2099-06-01T09:00:00",
    )
    mock_send.assert_awaited_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "anna@test.se"
    assert "Avbokning" in call_args[0][1]


async def test_email_disabled_skips_sending(mock_send, monkeypatch):
    """No email is sent when email_enabled=False."""
    monkeypatch.setattr("src.bookit.services.notification_service.settings.email_enabled", False)
    await send_booking_confirmation(
        customer_name="Anna",
        customer_email="anna@test.se",
        service_name="Klippning",
        slot_start="2099-06-01T09:00:00",
        slot_end="2099-06-01T10:00:00",
    )
    mock_send.assert_not_awaited()


async def test_email_error_does_not_propagate(_enable_email, monkeypatch):
    """An SMTP error must not raise — it's logged and swallowed."""
    with patch(
        "src.bookit.services.notification_service._send_email",
        new_callable=AsyncMock,
        side_effect=ConnectionRefusedError("SMTP down"),
    ):
        # Should NOT raise
        await send_booking_confirmation(
            customer_name="Anna",
            customer_email="anna@test.se",
            service_name="Klippning",
            slot_start="2099-06-01T09:00:00",
            slot_end="2099-06-01T10:00:00",
        )


async def test_booking_with_phone(test_client, sample_slot):
    """A booking with customer_phone stores and returns the phone."""
    resp = await test_client.post(
        "/api/bookings",
        json={
            "slot_id": sample_slot["id"],
            "customer_name": "Erik",
            "customer_email": "erik@test.se",
            "customer_phone": "+46701234567",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_phone"] == "+46701234567"


async def test_booking_without_phone(test_client, sample_slot):
    """Phone is optional — omitting it returns null."""
    resp = await test_client.post(
        "/api/bookings",
        json={
            "slot_id": sample_slot["id"],
            "customer_name": "Lisa",
            "customer_email": "lisa@test.se",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_phone"] is None
