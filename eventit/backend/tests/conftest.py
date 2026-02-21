"""Shared pytest fixtures for EventIt backend tests."""

from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from eventit.models.base import Base
from eventit.models.checkin import CheckIn  # noqa: F401
from eventit.models.event import Event  # noqa: F401
from eventit.models.tenant import Tenant  # noqa: F401
from eventit.models.ticket import Ticket, TicketTier  # noqa: F401


@pytest.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def test_client(test_session):
    from eventit.main import app
    from eventit.routers.checkin import get_db_dep as checkin_dep
    from eventit.routers.events import get_db_dep as events_dep
    from eventit.routers.public import get_db_dep as public_dep
    from eventit.routers.tenants import get_db_dep as tenants_dep
    from eventit.routers.tickets import get_db_dep as tickets_dep

    async def override_db():
        yield test_session

    app.dependency_overrides[tenants_dep] = override_db
    app.dependency_overrides[events_dep] = override_db
    app.dependency_overrides[public_dep] = override_db
    app.dependency_overrides[tickets_dep] = override_db
    app.dependency_overrides[checkin_dep] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_tenant(test_session):
    t = Tenant(slug="festival-ab", name="Festival AB")
    test_session.add(t)
    await test_session.flush()
    return t


@pytest.fixture
async def sample_event(test_session, sample_tenant):
    e = Event(
        tenant_id=sample_tenant.id,
        title="Summer Concert",
        slug="summer-concert-2026",
        description="An amazing outdoor concert",
        venue="Slottsparken, Malmö",
        start_time=datetime(2026, 7, 15, 18, 0, tzinfo=UTC),
        end_time=datetime(2026, 7, 15, 23, 0, tzinfo=UTC),
        capacity=500,
        status="draft",
    )
    test_session.add(e)
    await test_session.flush()
    return e


@pytest.fixture
async def published_event(test_session, sample_event):
    sample_event.status = "published"
    await test_session.flush()
    return sample_event


@pytest.fixture
async def sample_tier(test_session, published_event):
    tier = TicketTier(
        event_id=published_event.id,
        name="General",
        price_cents=29900,
        capacity=100,
    )
    test_session.add(tier)
    await test_session.flush()
    return tier
