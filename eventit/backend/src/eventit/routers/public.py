"""Public router — event pages + status transitions (no auth for MVP)."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.database import get_db
from eventit.schemas.event import EventRead, EventTransition
from eventit.schemas.ticket import TicketRead, TierRead
from eventit.services import event_service, ticket_service

router = APIRouter(prefix="/events", tags=["public"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.get("/public", response_model=list[EventRead])
async def list_published_events(session: AsyncSession = _db_dep) -> list[EventRead]:
    """List all published events for public browsing."""
    return await event_service.list_published_events(session)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, session: AsyncSession = _db_dep) -> EventRead:
    result = await event_service.get_event(session, event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.patch("/{event_id}/status", response_model=EventRead)
async def transition_event(
    event_id: int, payload: EventTransition, session: AsyncSession = _db_dep
) -> EventRead:
    try:
        return await event_service.transition_event(session, event_id, payload.status)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e


@router.get("/{event_id}/tiers", response_model=list[TierRead])
async def list_tiers(event_id: int, session: AsyncSession = _db_dep) -> list[TierRead]:
    return await ticket_service.list_tiers(session, event_id)


@router.get("/{event_id}/attendees", response_model=list[TicketRead])
async def list_attendees(event_id: int, session: AsyncSession = _db_dep) -> list[TicketRead]:
    return await ticket_service.list_attendees(session, event_id)
