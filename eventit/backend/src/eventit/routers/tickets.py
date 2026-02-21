"""Tickets router — purchase and tier management."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.database import get_db
from eventit.schemas.ticket import TicketPurchase, TicketRead, TierCreate, TierRead
from eventit.services import ticket_service

router = APIRouter(prefix="/events/{event_id}", tags=["tickets"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("/tiers", response_model=TierRead, status_code=201)
async def create_tier(
    event_id: int, payload: TierCreate, session: AsyncSession = _db_dep
) -> TierRead:
    try:
        return await ticket_service.create_tier(session, event_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/tickets", response_model=TicketRead, status_code=201)
async def purchase_ticket(
    event_id: int, payload: TicketPurchase, session: AsyncSession = _db_dep
) -> TicketRead:
    try:
        return await ticket_service.purchase_ticket(session, event_id, payload)
    except ValueError as e:
        status = 409 if "sold out" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e
