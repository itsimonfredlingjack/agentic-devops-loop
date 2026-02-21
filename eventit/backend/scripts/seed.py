"""Seed demo data for EventIt."""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eventit.models.base import Base
from eventit.models.event import Event, EventStatus
from eventit.models.tenant import Tenant
from eventit.models.ticket import TicketTier


async def seed() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///eventit_demo.db", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        # Create tenant
        tenant = Tenant(slug="demo-events", name="Demo Events AB")
        session.add(tenant)
        await session.flush()

        now = datetime.now(UTC)

        # Event 1: Tech Conference (published, upcoming)
        e1 = Event(
            tenant_id=tenant.id,
            title="Stockholm Tech Summit 2026",
            slug="stockholm-tech-summit-2026",
            description=(
                "The premier tech conference in the Nordics. "
                "Three days of talks, workshops, and networking."
            ),
            venue="Stockholmsmassan",
            start_time=now + timedelta(days=14),
            end_time=now + timedelta(days=16),
            status=EventStatus.published,
            capacity=500,
        )
        session.add(e1)
        await session.flush()

        t1_vip = TicketTier(
            event_id=e1.id, name="VIP", price_cents=299900, capacity=50, sold_count=12
        )
        t1_gen = TicketTier(
            event_id=e1.id, name="General", price_cents=99900, capacity=400, sold_count=187
        )
        t1_early = TicketTier(
            event_id=e1.id, name="Early Bird", price_cents=59900, capacity=50, sold_count=50
        )
        session.add_all([t1_vip, t1_gen, t1_early])

        # Event 2: Workshop (published, soon)
        e2 = Event(
            tenant_id=tenant.id,
            title="React & TypeScript Workshop",
            slug="react-typescript-workshop",
            description=(
                "Hands-on full-day workshop covering React 19, "
                "TypeScript 5.6, and modern state management."
            ),
            venue="SUP46, Stockholm",
            start_time=now + timedelta(days=7),
            end_time=now + timedelta(days=7, hours=8),
            status=EventStatus.published,
            capacity=30,
        )
        session.add(e2)
        await session.flush()

        t2_standard = TicketTier(
            event_id=e2.id, name="Standard", price_cents=149900, capacity=25, sold_count=18
        )
        t2_student = TicketTier(
            event_id=e2.id, name="Student", price_cents=49900, capacity=5, sold_count=3
        )
        session.add_all([t2_standard, t2_student])

        # Event 3: Concert (published)
        e3 = Event(
            tenant_id=tenant.id,
            title="Midsommar Live 2026",
            slug="midsommar-live-2026",
            description=(
                "Celebrate midsummer with live music at Skansen. "
                "Food trucks, dancing, and traditional festivities."
            ),
            venue="Skansen, Stockholm",
            start_time=now + timedelta(days=120),
            end_time=now + timedelta(days=120, hours=6),
            status=EventStatus.published,
            capacity=2000,
        )
        session.add(e3)
        await session.flush()

        t3_standing = TicketTier(
            event_id=e3.id, name="Standing", price_cents=39900, capacity=1500, sold_count=342
        )
        t3_seated = TicketTier(
            event_id=e3.id, name="Seated", price_cents=79900, capacity=400, sold_count=89
        )
        t3_vip = TicketTier(
            event_id=e3.id, name="VIP Lounge", price_cents=199900, capacity=100, sold_count=23
        )
        session.add_all([t3_standing, t3_seated, t3_vip])

        # Event 4: Draft event (admin only)
        e4 = Event(
            tenant_id=tenant.id,
            title="AI & Ethics Seminar",
            slug="ai-ethics-seminar",
            description="A half-day seminar exploring responsible AI development and deployment.",
            venue="KTH, Stockholm",
            start_time=now + timedelta(days=60),
            end_time=now + timedelta(days=60, hours=4),
            status=EventStatus.draft,
            capacity=100,
        )
        session.add(e4)
        await session.flush()

        t4_gen = TicketTier(
            event_id=e4.id, name="General", price_cents=0, capacity=100, sold_count=0
        )
        session.add(t4_gen)

        await session.commit()

    await engine.dispose()
    print("Seed complete: 1 tenant, 4 events, 10 tiers")


if __name__ == "__main__":
    asyncio.run(seed())
