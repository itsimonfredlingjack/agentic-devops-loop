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
    assert response.json() == {"status": "ok", "service": "trackit"}


# ────────────────────────────────────────────────
# Tenants
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_tenant(test_client):
    """POST /api/tenants creates a tenant and returns 201."""
    response = await test_client.post(
        "/api/tenants", json={"slug": "my-company", "name": "My Company"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Company"
    assert data["slug"] == "my-company"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_tenant_by_slug(test_client):
    """GET /api/tenants/{slug} returns the correct tenant."""
    await test_client.post("/api/tenants", json={"slug": "slug-test", "name": "Slug Test"})
    response = await test_client.get("/api/tenants/slug-test")
    assert response.status_code == 200
    assert response.json()["slug"] == "slug-test"


@pytest.mark.asyncio
async def test_get_tenant_not_found(test_client):
    """GET /api/tenants/{slug} with unknown slug returns 404."""
    response = await test_client.get("/api/tenants/does-not-exist")
    assert response.status_code == 404


# ────────────────────────────────────────────────
# Projects
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_project(test_client):
    """POST /api/tenants/{slug}/projects creates a project and returns 201."""
    await test_client.post("/api/tenants", json={"slug": "proj-co", "name": "Proj Co"})
    response = await test_client.post(
        "/api/tenants/proj-co/projects",
        json={"name": "API Work", "hourly_rate_cents": 150000},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Work"
    assert data["hourly_rate_cents"] == 150000


@pytest.mark.asyncio
async def test_create_project_tenant_not_found(test_client):
    """POST /api/tenants/{slug}/projects returns 404 if tenant doesn't exist."""
    response = await test_client.post(
        "/api/tenants/ghost/projects",
        json={"name": "X", "hourly_rate_cents": 10000},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_projects(test_client):
    """GET /api/tenants/{slug}/projects returns projects for that tenant."""
    await test_client.post("/api/tenants", json={"slug": "list-co", "name": "List Co"})
    await test_client.post(
        "/api/tenants/list-co/projects",
        json={"name": "P1", "hourly_rate_cents": 100000},
    )
    await test_client.post(
        "/api/tenants/list-co/projects",
        json={"name": "P2", "hourly_rate_cents": 200000},
    )
    response = await test_client.get("/api/tenants/list-co/projects")
    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert names == {"P1", "P2"}


@pytest.mark.asyncio
async def test_list_projects_tenant_not_found(test_client):
    """GET /api/tenants/{slug}/projects returns 404 if tenant doesn't exist."""
    response = await test_client.get("/api/tenants/ghost/projects")
    assert response.status_code == 404


# ────────────────────────────────────────────────
# Time entries
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_time_entry(test_client):
    """POST /api/tenants/{slug}/projects/{id}/time creates a time entry."""
    await test_client.post("/api/tenants", json={"slug": "time-co", "name": "Time Co"})
    r = await test_client.post(
        "/api/tenants/time-co/projects",
        json={"name": "Dev", "hourly_rate_cents": 100000},
    )
    project_id = r.json()["id"]

    response = await test_client.post(
        f"/api/tenants/time-co/projects/{project_id}/time",
        json={"date": "2025-01-15", "duration_minutes": 120},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["duration_minutes"] == 120
    assert data["is_billable"] is True
    assert data["is_invoiced"] is False


@pytest.mark.asyncio
async def test_log_time_tenant_not_found(test_client):
    """POST time entry with invalid tenant slug returns 404."""
    response = await test_client.post(
        "/api/tenants/ghost/projects/1/time",
        json={"date": "2025-01-15", "duration_minutes": 60},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_log_time_project_not_found(test_client):
    """POST time entry with invalid project id returns 404."""
    await test_client.post("/api/tenants", json={"slug": "time-co2", "name": "Time Co 2"})
    response = await test_client.post(
        "/api/tenants/time-co2/projects/9999/time",
        json={"date": "2025-01-15", "duration_minutes": 60},
    )
    assert response.status_code == 404


# ────────────────────────────────────────────────
# Full flow: tenant → project → time → invoice
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_time_tracking_flow(test_client):
    """End-to-end: create tenant → project → log time → get invoice → finalize."""
    # 1. Create tenant
    r = await test_client.post("/api/tenants", json={"slug": "flow-co", "name": "Flow Co"})
    assert r.status_code == 201

    # 2. Create project (1500 SEK/h = 150000 ore/h)
    r = await test_client.post(
        "/api/tenants/flow-co/projects",
        json={"name": "Consulting", "hourly_rate_cents": 150000},
    )
    assert r.status_code == 201
    project_id = r.json()["id"]

    # 3. Log 2h of time
    r = await test_client.post(
        f"/api/tenants/flow-co/projects/{project_id}/time",
        json={"date": "2025-03-10", "duration_minutes": 120},
    )
    assert r.status_code == 201

    # 4. Get invoice for March 2025
    r = await test_client.get("/api/tenants/flow-co/invoice", params={"year": 2025, "month": 3})
    assert r.status_code == 200
    inv = r.json()
    assert inv["subtotal_cents"] == 300000  # 2h * 150000
    assert inv["tax_amount_cents"] == 75000  # 25% of 300000
    assert inv["total_cents"] == 375000

    # 5. Finalize — marks entries as invoiced
    r = await test_client.post(
        "/api/tenants/flow-co/invoice/finalize", params={"year": 2025, "month": 3}
    )
    assert r.status_code == 200
    assert r.json()["entries_locked"] == 1

    # 6. Second invoice should be empty (all entries already invoiced)
    r = await test_client.get("/api/tenants/flow-co/invoice", params={"year": 2025, "month": 3})
    assert r.status_code == 200
    assert r.json()["subtotal_cents"] == 0
    assert r.json()["line_items"] == []
