"""QR check-in tests."""

import pytest


async def _buy_ticket(test_client, slug="ci-org"):
    """Full setup: tenant → published event → tier → ticket. Returns (event_id, qr_code)."""
    await test_client.post("/api/tenants", json={"slug": slug, "name": slug.title()})
    r = await test_client.post(
        f"/api/tenants/{slug}/events",
        json={
            "title": "Check-In Event",
            "slug": f"ci-event-{slug}",
            "start_time": "2026-09-15T18:00:00Z",
            "end_time": "2026-09-15T23:00:00Z",
        },
    )
    eid = r.json()["id"]
    await test_client.patch(f"/api/events/{eid}/status", json={"status": "published"})

    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "Standard", "price_cents": 19900, "capacity": 100},
    )
    tier_id = r.json()["id"]

    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={
            "tier_id": tier_id,
            "attendee_name": "Test Attendee",
            "attendee_email": "attendee@example.com",
        },
    )
    return eid, r.json()["qr_code"]


@pytest.mark.asyncio
async def test_check_in_success(test_client):
    _, qr = await _buy_ticket(test_client, "ci-ok")
    r = await test_client.post(f"/api/checkin/{qr}")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "checked_in"
    assert data["attendee_name"] == "Test Attendee"
    assert data["tier_name"] == "Standard"
    assert data["event_title"] == "Check-In Event"


@pytest.mark.asyncio
async def test_check_in_duplicate(test_client):
    """Can't check in the same ticket twice."""
    _, qr = await _buy_ticket(test_client, "ci-dup")

    r = await test_client.post(f"/api/checkin/{qr}")
    assert r.status_code == 200

    r = await test_client.post(f"/api/checkin/{qr}")
    assert r.status_code == 409
    assert "already" in r.json()["detail"]


@pytest.mark.asyncio
async def test_check_in_invalid_qr(test_client):
    r = await test_client.post("/api/checkin/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_lookup_ticket_by_qr(test_client):
    _, qr = await _buy_ticket(test_client, "ci-look")
    r = await test_client.get(f"/api/checkin/{qr}")
    assert r.status_code == 200
    assert r.json()["qr_code"] == qr
    assert r.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_full_event_flow(test_client):
    """Full flow: create → publish → sell tickets → check in → verify attendees."""
    await test_client.post("/api/tenants", json={"slug": "flow-org", "name": "Flow Org"})

    # Create event
    r = await test_client.post(
        "/api/tenants/flow-org/events",
        json={
            "title": "Full Flow Concert",
            "slug": "full-flow",
            "venue": "Globen, Stockholm",
            "start_time": "2026-12-01T19:00:00Z",
            "end_time": "2026-12-02T01:00:00Z",
            "capacity": 1000,
        },
    )
    eid = r.json()["id"]

    # Publish
    await test_client.patch(f"/api/events/{eid}/status", json={"status": "published"})

    # Add tiers
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "VIP", "price_cents": 149900, "capacity": 50},
    )
    vip_id = r.json()["id"]
    r = await test_client.post(
        f"/api/events/{eid}/tiers",
        json={"name": "General", "price_cents": 49900, "capacity": 500},
    )
    gen_id = r.json()["id"]

    # Buy tickets
    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={"tier_id": vip_id, "attendee_name": "VIP Person", "attendee_email": "vip@x.com"},
    )
    vip_qr = r.json()["qr_code"]

    r = await test_client.post(
        f"/api/events/{eid}/tickets",
        json={
            "tier_id": gen_id,
            "attendee_name": "Regular Person",
            "attendee_email": "reg@x.com",
        },
    )
    _ = r.json()["qr_code"]

    # Check in VIP
    r = await test_client.post(f"/api/checkin/{vip_qr}")
    assert r.json()["tier_name"] == "VIP"
    assert r.json()["status"] == "checked_in"

    # Check attendees
    r = await test_client.get(f"/api/events/{eid}/attendees")
    assert len(r.json()) == 2

    # Verify tiers show sold count
    r = await test_client.get(f"/api/events/{eid}/tiers")
    tiers = {t["name"]: t for t in r.json()}
    assert tiers["VIP"]["sold_count"] == 1
    assert tiers["General"]["sold_count"] == 1

    # Complete event
    r = await test_client.patch(f"/api/events/{eid}/status", json={"status": "completed"})
    assert r.json()["status"] == "completed"
