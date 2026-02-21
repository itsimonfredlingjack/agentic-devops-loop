"""Payments router — Stripe Checkout Sessions and webhook handling."""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from storeit.config import settings
from storeit.database import get_db
from storeit.models.order import Order
from storeit.services import payment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


class CheckoutRequest(BaseModel):
    order_id: int = Field(..., ge=1)


class CheckoutResponse(BaseModel):
    checkout_session_id: str
    checkout_url: str


@router.post("/checkout", response_model=CheckoutResponse, status_code=201)
async def create_checkout(
    payload: CheckoutRequest,
    session: AsyncSession = _db_dep,
) -> CheckoutResponse:
    """Create a Stripe Checkout Session for an existing order.

    The order must be in 'pending' status. Stores the Stripe session ID
    on the order for webhook correlation.
    """
    if not settings.stripe_enabled:
        raise HTTPException(status_code=503, detail="Stripe payments are not enabled")

    result = await session.execute(
        select(Order).where(Order.id == payload.order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Order is '{order.status}', expected 'pending'"
        )

    line_items = [
        {
            "name": item.product_name,
            "price_cents": item.unit_price_cents,
            "quantity": item.quantity,
        }
        for item in order.items
    ]

    stripe_session = payment_service.create_checkout_session(
        order_id=order.id,
        line_items=line_items,
        customer_email=order.customer_email,
        total_cents=order.total_cents,
    )

    order.stripe_session_id = stripe_session.id
    await session.flush()

    return CheckoutResponse(
        checkout_session_id=stripe_session.id,
        checkout_url=stripe_session.url,
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = _db_dep,
) -> dict[str, bool]:
    """Handle Stripe webhook events.

    IMPORTANT: Uses raw request body for signature verification.
    Never parse JSON before verifying the signature.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = payment_service.verify_webhook_signature(payload, sig_header)
    except Exception as e:
        logger.warning("Stripe webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    if event["type"] == "checkout.session.completed":
        stripe_session_id = event["data"]["object"]["id"]
        order = await payment_service.fulfill_checkout(session, stripe_session_id)
        if order:
            logger.info("Fulfilled order %d via Stripe webhook", order.id)
        else:
            # Return 500 so Stripe retries — order may not exist yet
            logger.warning("No order for Stripe session %s — will retry", stripe_session_id)
            raise HTTPException(status_code=500, detail="Order not found, retry later")

    return {"received": True}
