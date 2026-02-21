"""Stripe payment service — Checkout Sessions and webhook fulfillment.

Uses Stripe Checkout Sessions API (not Payment Intents directly).
All fulfillment is webhook-driven and idempotent.
"""

import logging

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from storeit.config import settings
from storeit.models.inventory import InventoryReservation
from storeit.models.order import Order, OrderStatus
from storeit.services.inventory_service import fulfill_reservation

logger = logging.getLogger(__name__)


def _configure_stripe() -> None:
    stripe.api_key = settings.stripe_secret_key


def create_checkout_session(
    *,
    order_id: int,
    line_items: list[dict],
    customer_email: str,
    total_cents: int,
) -> stripe.checkout.Session:
    """Create a Stripe Checkout Session for an order.

    Args:
        order_id: The order ID to associate with this payment.
        line_items: List of dicts with name, price_cents, quantity.
        customer_email: Pre-fill email on Stripe Checkout page.
        total_cents: Total in cents (for metadata).

    Returns:
        A Stripe Checkout Session object with .id and .url.
    """
    _configure_stripe()
    stripe_line_items = [
        {
            "price_data": {
                "currency": "sek",
                "unit_amount": item["price_cents"],
                "product_data": {"name": item["name"]},
            },
            "quantity": item["quantity"],
        }
        for item in line_items
    ]

    session = stripe.checkout.Session.create(
        line_items=stripe_line_items,
        mode="payment",
        customer_email=customer_email,
        metadata={"order_id": str(order_id), "total_cents": str(total_cents)},
        success_url=f"{settings.frontend_url}/orders/{order_id}/success"
        + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=f"{settings.frontend_url}/orders/{order_id}/cancelled",
    )
    return session


def verify_webhook_signature(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event.

    Args:
        payload: Raw request body bytes (NOT parsed JSON).
        sig_header: Value of the Stripe-Signature header.

    Returns:
        The parsed Stripe event as a dict.

    Raises:
        stripe.error.SignatureVerificationError: If verification fails.
    """
    _configure_stripe()
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)


async def fulfill_checkout(session: AsyncSession, stripe_session_id: str) -> Order | None:
    """Fulfill an order after successful Stripe payment.

    Idempotent: if the order is already paid, returns it without changes.
    Transitions order from pending → paid and fulfills all inventory reservations.

    Returns None if no order found for the given Stripe session ID.
    """
    result = await session.execute(
        select(Order)
        .where(Order.stripe_session_id == stripe_session_id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        return None

    # Idempotent: already fulfilled
    if order.status != OrderStatus.pending:
        return order

    # Transition to paid
    order.status = OrderStatus.paid

    # Fulfill inventory reservations linked to this order via cart_id="order-{id}"
    reservation_key = f"order-{order.id}"
    reservations = await session.execute(
        select(InventoryReservation).where(
            InventoryReservation.cart_id == reservation_key,
            InventoryReservation.status == "active",
        )
    )
    for reservation in reservations.scalars().all():
        await fulfill_reservation(session, reservation.id)

    await session.flush()
    return order
