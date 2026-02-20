"""Payments router — Stripe Checkout integration."""

import logging

import aiosqlite
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.bookit.config import settings
from src.bookit.database import get_db
from src.bookit.services.payment_service import (
    create_checkout_session,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


# ────────────────────────────────────────────────
# POST /api/bookings/checkout
# ────────────────────────────────────────────────


class CheckoutCreate(BaseModel):
    """Payload for initiating Stripe Checkout."""

    slot_id: int = Field(..., ge=1)
    customer_name: str = Field(..., min_length=1)
    customer_email: str
    customer_phone: str | None = None
    tenant_slug: str = Field(..., min_length=1)


class CheckoutResponse(BaseModel):
    """Response from creating a checkout session."""

    checkout_url: str
    session_id: str
    booking_id: int


@router.post("/bookings/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> CheckoutResponse:
    """Create a booking + Stripe Checkout session (for paid services).

    For free services (price_cents=0) this endpoint returns 400 —
    use the regular POST /api/bookings endpoint instead.
    """
    if not settings.stripe_enabled:
        raise HTTPException(status_code=400, detail="Stripe is not enabled")

    # Look up slot and service
    cursor = await db.execute(
        "SELECT s.*, svc.name AS service_name, svc.price_cents "
        "FROM slots s JOIN services svc ON s.service_id = svc.id "
        "WHERE s.id = ?",
        (payload.slot_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Slot not found")

    if row["price_cents"] <= 0:
        raise HTTPException(status_code=400, detail="This service is free — use regular booking")

    if row["booked_count"] >= row["capacity"]:
        raise HTTPException(status_code=409, detail="No remaining capacity for this slot")

    # Create a pending booking
    cursor = await db.execute(
        "INSERT INTO bookings "
        "(slot_id, customer_name, customer_email, customer_phone, "
        "status, payment_status) "
        "VALUES (?, ?, ?, ?, 'pending', 'pending')",
        (
            payload.slot_id,
            payload.customer_name,
            payload.customer_email,
            payload.customer_phone,
        ),
    )
    booking_id = cursor.lastrowid
    await db.commit()

    # Create Stripe session
    session = await create_checkout_session(
        booking_id=booking_id,
        service_name=row["service_name"],
        price_cents=row["price_cents"],
        customer_email=payload.customer_email,
        tenant_slug=payload.tenant_slug,
    )

    # Store session ID on booking
    await db.execute(
        "UPDATE bookings SET stripe_session_id = ? WHERE id = ?",
        (session.id, booking_id),
    )
    await db.commit()

    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.id,
        booking_id=booking_id,
    )


# ────────────────────────────────────────────────
# POST /api/webhooks/stripe
# ────────────────────────────────────────────────


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> dict[str, str]:
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, sig)
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session.get("metadata", {}).get("booking_id")
        if booking_id:
            await db.execute(
                "UPDATE bookings SET status = 'confirmed', payment_status = 'paid' WHERE id = ?",
                (int(booking_id),),
            )
            # Increment booked_count
            cursor = await db.execute(
                "SELECT slot_id FROM bookings WHERE id = ?",
                (int(booking_id),),
            )
            brow = await cursor.fetchone()
            if brow:
                await db.execute(
                    "UPDATE slots SET booked_count = booked_count + 1 WHERE id = ?",
                    (brow["slot_id"],),
                )
            await db.commit()
            logger.info("Payment confirmed for booking %s", booking_id)

    return {"status": "ok"}


# ────────────────────────────────────────────────
# GET /api/bookings/checkout/{session_id}/status
# ────────────────────────────────────────────────


class CheckoutStatus(BaseModel):
    """Status of a checkout session's associated booking."""

    booking_id: int | None = None
    payment_status: str
    booking_status: str


@router.get(
    "/bookings/checkout/{session_id}/status",
    response_model=CheckoutStatus,
)
async def get_checkout_status(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> CheckoutStatus:
    """Poll the status of a booking by its Stripe session ID."""
    cursor = await db.execute(
        "SELECT id, payment_status, status FROM bookings WHERE stripe_session_id = ?",
        (session_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return CheckoutStatus(
        booking_id=row["id"],
        payment_status=row["payment_status"],
        booking_status=row["status"],
    )
