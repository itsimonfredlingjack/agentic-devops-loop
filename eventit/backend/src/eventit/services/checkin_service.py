"""Check-in service — QR scan validation and recording."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eventit.models.checkin import CheckIn
from eventit.models.event import Event
from eventit.models.ticket import Ticket, TicketStatus
from eventit.schemas.checkin import CheckInResponse


async def check_in(session: AsyncSession, qr_code: str) -> CheckInResponse:
    """Validate a QR code and record check-in.

    Raises ValueError if ticket not found, already checked in, or cancelled.
    """
    result = await session.execute(
        select(Ticket).where(Ticket.qr_code == qr_code).options(selectinload(Ticket.tier))
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise ValueError("Invalid QR code — ticket not found")

    if ticket.status == TicketStatus.checked_in:
        raise ValueError("Ticket already checked in")

    if ticket.status == TicketStatus.cancelled:
        raise ValueError("Ticket has been cancelled")

    # Get event info via tier
    tier = ticket.tier
    event = await session.get(Event, tier.event_id)

    # Record check-in
    ticket.status = TicketStatus.checked_in
    checkin = CheckIn(ticket_id=ticket.id)
    session.add(checkin)
    await session.flush()

    return CheckInResponse(
        status="checked_in",
        ticket_id=ticket.id,
        attendee_name=ticket.attendee_name,
        attendee_email=ticket.attendee_email,
        tier_name=tier.name,
        event_title=event.title if event else "Unknown",
        checked_in_at=checkin.checked_in_at,
    )
