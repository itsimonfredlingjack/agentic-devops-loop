"""Event service — CRUD + state machine."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eventit.models.event import EVENT_TRANSITIONS, Event, EventStatus
from eventit.models.tenant import Tenant
from eventit.schemas.event import EventCreate, EventRead


async def create_event(session: AsyncSession, tenant_slug: str, payload: EventCreate) -> EventRead:
    tenant = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    t = tenant.scalar_one_or_none()
    if t is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    existing = await session.execute(select(Event).where(Event.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Event slug '{payload.slug}' already exists")

    event = Event(
        tenant_id=t.id,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        venue=payload.venue,
        start_time=payload.start_time,
        end_time=payload.end_time,
        capacity=payload.capacity,
        status=EventStatus.draft,
    )
    session.add(event)
    await session.flush()
    return EventRead.model_validate(event)


async def list_events(session: AsyncSession, tenant_slug: str) -> list[EventRead]:
    tenant = await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    t = tenant.scalar_one_or_none()
    if t is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    result = await session.execute(
        select(Event).where(Event.tenant_id == t.id).order_by(Event.start_time)
    )
    return [EventRead.model_validate(e) for e in result.scalars().all()]


async def get_event(session: AsyncSession, event_id: int) -> EventRead | None:
    result = await session.execute(
        select(Event).where(Event.id == event_id).options(selectinload(Event.tiers))
    )
    event = result.scalar_one_or_none()
    if event is None:
        return None
    return EventRead.model_validate(event)


async def transition_event(session: AsyncSession, event_id: int, new_status_str: str) -> EventRead:
    event = await session.get(Event, event_id)
    if event is None:
        raise ValueError(f"Event {event_id} not found")

    try:
        new_status = EventStatus(new_status_str)
    except ValueError:
        raise ValueError(f"Invalid status: {new_status_str}") from None

    current = EventStatus(event.status)
    allowed = EVENT_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition event {event_id} from {current} to {new_status}. "
            f"Allowed: {sorted(s.value for s in allowed)}"
        )

    event.status = new_status.value
    await session.flush()
    return EventRead.model_validate(event)
