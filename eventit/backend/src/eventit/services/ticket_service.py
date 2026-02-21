"""Ticket service — purchase with SELECT FOR UPDATE + QR generation."""

import base64
import io
import uuid

import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eventit.models.event import Event, EventStatus
from eventit.models.ticket import Ticket, TicketTier
from eventit.schemas.ticket import TicketPurchase, TicketRead, TierCreate, TierRead


def _generate_qr_b64(data: str) -> str:
    """Generate a QR code PNG as base64 string."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


async def create_tier(session: AsyncSession, event_id: int, payload: TierCreate) -> TierRead:
    """Add a ticket tier to an event."""
    event = await session.get(Event, event_id)
    if event is None:
        raise ValueError(f"Event {event_id} not found")

    tier = TicketTier(
        event_id=event_id,
        name=payload.name,
        price_cents=payload.price_cents,
        capacity=payload.capacity,
    )
    session.add(tier)
    await session.flush()
    return TierRead.model_validate(tier)


async def list_tiers(session: AsyncSession, event_id: int) -> list[TierRead]:
    """List all tiers for an event."""
    result = await session.execute(
        select(TicketTier).where(TicketTier.event_id == event_id).order_by(TicketTier.price_cents)
    )
    return [TierRead.model_validate(t) for t in result.scalars().all()]


async def purchase_ticket(
    session: AsyncSession, event_id: int, payload: TicketPurchase
) -> TicketRead:
    """Purchase a ticket with SELECT FOR UPDATE to prevent overselling.

    Locks the tier row, checks capacity, increments sold_count, generates QR code.
    """
    # Verify event is published
    event = await session.get(Event, event_id)
    if event is None:
        raise ValueError(f"Event {event_id} not found")
    if event.status != EventStatus.published:
        raise ValueError(f"Event is '{event.status}', tickets only available when published")

    # Lock tier row
    result = await session.execute(
        select(TicketTier)
        .where(TicketTier.id == payload.tier_id, TicketTier.event_id == event_id)
        .with_for_update()
    )
    tier = result.scalar_one_or_none()
    if tier is None:
        raise ValueError(f"Tier {payload.tier_id} not found for event {event_id}")

    if tier.sold_count >= tier.capacity:
        raise ValueError(f"Tier '{tier.name}' is sold out (capacity: {tier.capacity})")

    # Generate unique QR code
    qr_uuid = str(uuid.uuid4())
    qr_image = _generate_qr_b64(qr_uuid)

    ticket = Ticket(
        tier_id=tier.id,
        attendee_name=payload.attendee_name,
        attendee_email=payload.attendee_email,
        qr_code=qr_uuid,
        qr_image_b64=qr_image,
        status="confirmed",
    )
    session.add(ticket)

    tier.sold_count += 1
    await session.flush()

    return TicketRead.model_validate(ticket)


async def get_ticket_by_qr(session: AsyncSession, qr_code: str) -> Ticket | None:
    """Look up a ticket by its QR code UUID."""
    result = await session.execute(
        select(Ticket).where(Ticket.qr_code == qr_code).options(selectinload(Ticket.tier))
    )
    return result.scalar_one_or_none()


async def list_attendees(session: AsyncSession, event_id: int) -> list[TicketRead]:
    """List all confirmed/checked-in tickets for an event."""
    result = await session.execute(
        select(Ticket)
        .join(TicketTier)
        .where(
            TicketTier.event_id == event_id,
            Ticket.status.in_(["confirmed", "checked_in"]),
        )
        .order_by(Ticket.attendee_name)
    )
    return [TicketRead.model_validate(t) for t in result.scalars().all()]
