"""Integration tests — full HTTP round-trip via test_client."""

import pytest

# ────────────────────────────────────────────────
# Health
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    """GET /health returns 200 with status ok."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ────────────────────────────────────────────────
# Tenants
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_tenant(test_client):
    """POST /tenants creates a tenant and returns 201."""
    response = await test_client.post("/api/tenants", json={"name": "My Barbershop"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Barbershop"
    assert data["slug"] == "my-barbershop"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(test_client):
    """POST /tenants with duplicate name returns 409."""
    await test_client.post("/api/tenants", json={"name": "Dupe Shop"})
    response = await test_client.post("/api/tenants", json={"name": "Dupe Shop"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_tenant_not_found(test_client):
    """GET /tenants/{slug} with unknown slug returns 404."""
    response = await test_client.get("/api/tenants/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tenant_by_slug(test_client):
    """GET /tenants/{slug} returns the correct tenant."""
    await test_client.post("/api/tenants", json={"name": "Slug Test Shop"})
    response = await test_client.get("/api/tenants/slug-test-shop")
    assert response.status_code == 200
    assert response.json()["slug"] == "slug-test-shop"


# ────────────────────────────────────────────────
# Full booking flow
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_booking_flow(test_client):
    """End-to-end: create tenant → service → slot → book → verify → cancel."""

    # 1. Create tenant
    r = await test_client.post("/api/tenants", json={"name": "Flow Salon"})
    assert r.status_code == 201
    slug = r.json()["slug"]

    # 2. Create service
    r = await test_client.post(
        f"/api/tenants/{slug}/services",
        json={"name": "Massage", "duration_min": 60, "capacity": 3},
    )
    assert r.status_code == 201
    service_id = r.json()["id"]

    # 3. Generate slots
    r = await test_client.post(
        f"/api/tenants/{slug}/services/{service_id}/slots/generate",
        json={
            "date": "2099-06-15",
            "start_hour": 9,
            "end_hour": 12,
            "interval_min": 60,
            "capacity": 3,
        },
    )
    assert r.status_code == 201
    slots = r.json()
    assert len(slots) == 3  # 9-10, 10-11, 11-12

    # 4. List available slots (should return all 3)
    r = await test_client.get(
        f"/api/tenants/{slug}/services/{service_id}/slots",
        params={"date": "2099-06-15"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 3

    # 5. Book a slot
    slot_id = slots[0]["id"]
    r = await test_client.post(
        "/api/bookings",
        json={
            "slot_id": slot_id,
            "customer_name": "Ada Lovelace",
            "customer_email": "ada@example.com",
        },
    )
    assert r.status_code == 201
    booking = r.json()
    assert booking["status"] == "confirmed"
    booking_id = booking["id"]

    # 6. Verify booking appears in email list
    r = await test_client.get("/api/bookings", params={"email": "ada@example.com"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    # 7. Cancel the booking
    r = await test_client.delete(f"/api/bookings/{booking_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    # 8. Slot should be fully available again
    r = await test_client.get(
        f"/api/tenants/{slug}/services/{service_id}/slots",
        params={"date": "2099-06-15"},
    )
    assert len(r.json()) == 3


# ────────────────────────────────────────────────
# Services
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_services(test_client):
    """GET /tenants/{slug}/services returns services for that tenant only."""
    await test_client.post("/api/tenants", json={"name": "Service Test Tenant"})
    slug = "service-test-tenant"

    await test_client.post(f"/api/tenants/{slug}/services", json={"name": "Cut"})
    await test_client.post(f"/api/tenants/{slug}/services", json={"name": "Shave"})

    r = await test_client.get(f"/api/tenants/{slug}/services")
    assert r.status_code == 200
    names = {s["name"] for s in r.json()}
    assert "Cut" in names
    assert "Shave" in names


# ────────────────────────────────────────────────
# Slots
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_slot_via_api(test_client):
    """POST /tenants/{slug}/services/{id}/slots creates an individual slot."""
    await test_client.post("/api/tenants", json={"name": "Slot API Tenant"})
    slug = "slot-api-tenant"
    r = await test_client.post(f"/api/tenants/{slug}/services", json={"name": "Trim"})
    service_id = r.json()["id"]

    r = await test_client.post(
        f"/api/tenants/{slug}/services/{service_id}/slots",
        json={"start_time": "2099-07-01T14:00:00", "end_time": "2099-07-01T15:00:00"},
    )
    assert r.status_code == 201
    slot = r.json()
    assert slot["available"] is True


@pytest.mark.asyncio
async def test_booking_capacity_409_via_api(test_client):
    """POST /bookings returns 409 when slot has no remaining capacity."""
    await test_client.post("/api/tenants", json={"name": "Cap Test Tenant"})
    slug = "cap-test-tenant"
    r = await test_client.post(
        f"/api/tenants/{slug}/services", json={"name": "Cap Service", "capacity": 1}
    )
    service_id = r.json()["id"]

    r = await test_client.post(
        f"/api/tenants/{slug}/services/{service_id}/slots",
        json={
            "start_time": "2099-08-01T09:00:00",
            "end_time": "2099-08-01T10:00:00",
            "capacity": 1,
        },
    )
    slot_id = r.json()["id"]

    # First booking succeeds
    r = await test_client.post(
        "/api/bookings",
        json={"slot_id": slot_id, "customer_name": "A", "customer_email": "a@ex.com"},
    )
    assert r.status_code == 201

    # Second booking must fail
    r = await test_client.post(
        "/api/bookings",
        json={"slot_id": slot_id, "customer_name": "B", "customer_email": "b@ex.com"},
    )
    assert r.status_code == 409
