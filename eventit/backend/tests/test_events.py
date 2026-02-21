"""Event CRUD and state machine tests."""

import pytest


@pytest.mark.asyncio
async def test_health(test_client):
    r = await test_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "eventit"}


@pytest.mark.asyncio
async def test_create_tenant(test_client):
    r = await test_client.post("/api/tenants", json={"slug": "org-1", "name": "Org One"})
    assert r.status_code == 201
    assert r.json()["slug"] == "org-1"


@pytest.mark.asyncio
async def test_get_tenant_not_found(test_client):
    r = await test_client.get("/api/tenants/ghost")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_event(test_client):
    await test_client.post("/api/tenants", json={"slug": "evt-org", "name": "Evt Org"})
    r = await test_client.post(
        "/api/tenants/evt-org/events",
        json={
            "title": "Workshop",
            "slug": "workshop-2026",
            "start_time": "2026-09-01T10:00:00Z",
            "end_time": "2026-09-01T16:00:00Z",
            "capacity": 30,
        },
    )
    assert r.status_code == 201
    assert r.json()["title"] == "Workshop"
    assert r.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_list_events(test_client):
    await test_client.post("/api/tenants", json={"slug": "list-org", "name": "List Org"})
    await test_client.post(
        "/api/tenants/list-org/events",
        json={
            "title": "E1",
            "slug": "e1",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T12:00:00Z",
        },
    )
    r = await test_client.get("/api/tenants/list-org/events")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_get_event_public(test_client):
    await test_client.post("/api/tenants", json={"slug": "pub-org", "name": "Pub Org"})
    r = await test_client.post(
        "/api/tenants/pub-org/events",
        json={
            "title": "Public Event",
            "slug": "pub-event",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T12:00:00Z",
        },
    )
    eid = r.json()["id"]
    r = await test_client.get(f"/api/events/{eid}")
    assert r.status_code == 200
    assert r.json()["title"] == "Public Event"


@pytest.mark.asyncio
async def test_event_state_machine(test_client):
    await test_client.post("/api/tenants", json={"slug": "sm-org", "name": "SM Org"})
    r = await test_client.post(
        "/api/tenants/sm-org/events",
        json={
            "title": "State Machine Event",
            "slug": "sm-event",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T12:00:00Z",
        },
    )
    eid = r.json()["id"]

    # draft -> published
    r = await test_client.patch(f"/api/events/{eid}/status", json={"status": "published"})
    assert r.status_code == 200
    assert r.json()["status"] == "published"

    # published -> completed
    r = await test_client.patch(f"/api/events/{eid}/status", json={"status": "completed"})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_invalid_transition(test_client):
    await test_client.post("/api/tenants", json={"slug": "inv-org", "name": "Inv Org"})
    r = await test_client.post(
        "/api/tenants/inv-org/events",
        json={
            "title": "Bad Transition",
            "slug": "bad-trans",
            "start_time": "2026-06-01T10:00:00Z",
            "end_time": "2026-06-01T12:00:00Z",
        },
    )
    eid = r.json()["id"]

    # draft -> completed is not allowed
    r = await test_client.patch(f"/api/events/{eid}/status", json={"status": "completed"})
    assert r.status_code == 400
