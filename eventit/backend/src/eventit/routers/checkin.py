"""Check-in router — QR code scan endpoint."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.database import get_db
from eventit.schemas.checkin import CheckInResponse
from eventit.schemas.ticket import TicketRead
from eventit.services import checkin_service, ticket_service

router = APIRouter(prefix="/checkin", tags=["check-in"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("/{qr_code}", response_model=CheckInResponse)
async def scan_checkin(qr_code: str, session: AsyncSession = _db_dep) -> CheckInResponse:
    """Scan a QR code to check in an attendee."""
    try:
        return await checkin_service.check_in(session, qr_code)
    except ValueError as e:
        status = 409 if "already" in str(e) else 404
        raise HTTPException(status_code=status, detail=str(e)) from e


@router.get("/{qr_code}", response_model=TicketRead)
async def lookup_ticket(qr_code: str, session: AsyncSession = _db_dep) -> TicketRead:
    """Look up a ticket by QR code without checking in."""
    ticket = await ticket_service.get_ticket_by_qr(session, qr_code)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketRead.model_validate(ticket)
