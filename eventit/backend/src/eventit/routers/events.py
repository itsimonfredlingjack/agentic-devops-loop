"""Events router."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.database import get_db
from eventit.schemas.event import EventCreate, EventRead
from eventit.services import event_service

router = APIRouter(prefix="/tenants/{slug}/events", tags=["events"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("", response_model=EventRead, status_code=201)
async def create_event(
    slug: str, payload: EventCreate, session: AsyncSession = _db_dep
) -> EventRead:
    try:
        return await event_service.create_event(session, slug, payload)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 409
        raise HTTPException(status_code=status, detail=str(e)) from e


@router.get("", response_model=list[EventRead])
async def list_events(slug: str, session: AsyncSession = _db_dep) -> list[EventRead]:
    try:
        return await event_service.list_events(session, slug)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
