"""Stripe payment service for checkout sessions and webhook handling."""

import logging

import stripe

from src.bookit.config import settings

logger = logging.getLogger(__name__)


def _configure_stripe() -> None:
    """Set the Stripe API key from settings."""
    stripe.api_key = settings.stripe_secret_key


async def create_checkout_session(
    *,
    booking_id: int,
    service_name: str,
    price_cents: int,
    customer_email: str,
    tenant_slug: str,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout Session for a booking.

    Args:
        booking_id: The booking ID to associate with this payment.
        service_name: Name of the service being booked.
        price_cents: Price in the smallest currency unit (öre for SEK).
        customer_email: Pre-fill the email on the Stripe Checkout page.
        tenant_slug: Used to build success/cancel URLs.

    Returns:
        A Stripe Checkout Session object.
    """
    _configure_stripe()
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "sek",
                    "unit_amount": price_cents,
                    "product_data": {"name": service_name},
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        customer_email=customer_email,
        metadata={"booking_id": str(booking_id)},
        success_url=(
            f"{settings.frontend_url}/book/{tenant_slug}/success?session_id={{CHECKOUT_SESSION_ID}}"
        ),
        cancel_url=f"{settings.frontend_url}/book/{tenant_slug}",
    )
    return session


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event.

    Args:
        payload: Raw request body bytes.
        sig_header: Value of the ``Stripe-Signature`` header.

    Returns:
        The parsed Stripe event as a dict.

    Raises:
        stripe.error.SignatureVerificationError: If verification fails.
    """
    _configure_stripe()
    event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    return event
