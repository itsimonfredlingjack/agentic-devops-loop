"""Ticket purchase and tier tests."""

import pytest


async def _setup_published_event(test_client, slug="tix-org"):
    """Create tenant + published event. Returns event_id."""
    await test_client.post("/api/tenants", json={"slug": slug, "name": slug.title()})
    r = await test_client.post(
        f"/api/tenants/{slug}/events",
        json={
            "title": "Ticket Event",
            "slug": f"tix-event-{slug}",
            "start_time": "2026-08-01T18:00:00Z",
            "end_time": "2026-08-01T23:00:00Z",
            "capacity": 200,
        },
    )
    eid = r.json()["id"]
    await test_client.patch(f"/api/events/{eid}/status", json={"status": "published"})
    return eid


@pytest.mark.asyncio
async def test_create_tier(test_client):
    eid = await _setup_published_event(test_client, "tier-org")
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "VIP", "price_cents": 99900, "capacity": 50},
    )
    assert r.status_code == 201
    assert r.json()["name"] == "VIP"
    assert r.json()["price_cents"] == 99900
    assert r.json()["sold_count"] == 0


@pytest.mark.asyncio
async def test_purchase_ticket(test_client):
    eid = await _setup_published_event(test_client, "buy-org")
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "General", "price_cents": 29900, "capacity": 100},
    )
    tier_id = r.json()["id"]

    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={
            "tier_id": tier_id,
            "attendee_name": "Anna Svensson",
            "attendee_email": "anna@example.com",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["attendee_name"] == "Anna Svensson"
    assert data["status"] == "confirmed"
    assert len(data["qr_code"]) == 36  # UUID format


@pytest.mark.asyncio
async def test_purchase_ticket_sold_out(test_client):
    eid = await _setup_published_event(test_client, "sold-org")
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "Limited", "price_cents": 50000, "capacity": 1},
    )
    tier_id = r.json()["id"]

    # First ticket succeeds
    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={"tier_id": tier_id, "attendee_name": "A", "attendee_email": "a@x.com"},
    )
    assert r.status_code == 201

    # Second ticket fails — sold out
    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={"tier_id": tier_id, "attendee_name": "B", "attendee_email": "b@x.com"},
    )
    assert r.status_code == 409
    assert "sold out" in r.json()["detail"]


@pytest.mark.asyncio
async def test_purchase_ticket_draft_event(test_client):
    """Can't buy tickets for unpublished events."""
    await test_client.post("/api/tenants", json={"slug": "draft-org", "name": "Draft Org"})
    r = await test_client.post(
        "/api/tenants/draft-org/events",
        json={
            "title": "Draft",
            "slug": "draft-event",
            "start_time": "2026-08-01T10:00:00Z",
            "end_time": "2026-08-01T12:00:00Z",
        },
    )
    eid = r.json()["id"]
    # Don't publish — leave as draft

    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "Gen", "price_cents": 10000, "capacity": 50},
    )
    tier_id = r.json()["id"]

    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={"tier_id": tier_id, "attendee_name": "X", "attendee_email": "x@x.com"},
    )
    assert r.status_code == 400
    assert "published" in r.json()["detail"]


@pytest.mark.asyncio
async def test_list_attendees(test_client):
    eid = await _setup_published_event(test_client, "att-org")
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "Gen", "price_cents": 15000, "capacity": 50},
    )
    tier_id = r.json()["id"]

    for name in ["Alice", "Bob", "Charlie"]:
        await test_client.post(
            f"/api/events/{eid}/tickets",
            json={
                "tier_id": tier_id,
                "attendee_name": name,
                "attendee_email": f"{name.lower()}@x.com",
            },
        )

    r = await test_client.get(f"/api/events/{eid}/attendees")
    assert r.status_code == 200
    assert len(r.json()) == 3
