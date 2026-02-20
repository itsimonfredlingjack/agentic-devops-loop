"""Tests for statistics dashboard."""


async def test_stats_zero_data(test_client, sample_tenant):
    """Stats endpoint returns zero values when no bookings exist."""
    resp = await test_client.get(f"/api/tenants/{sample_tenant['slug']}/stats?period=month")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_bookings"] == 0
    assert data["confirmed_bookings"] == 0
    assert data["cancelled_bookings"] == 0
    assert data["total_revenue_cents"] == 0
    assert data["services"] == []
    assert data["period"] == "month"


async def test_stats_with_bookings(test_client, sample_slot, sample_tenant):
    """Stats reflect actual bookings and revenue."""
    # Create a booking
    resp = await test_client.post(
        "/api/bookings",
        json={
            "slot_id": sample_slot["id"],
            "customer_name": "Anna",
            "customer_email": "anna@test.se",
        },
    )
    assert resp.status_code == 201

    resp = await test_client.get(f"/api/tenants/{sample_tenant['slug']}/stats?period=year")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_bookings"] == 1
    assert data["confirmed_bookings"] == 1
    assert data["cancelled_bookings"] == 0
    assert len(data["services"]) == 1
    assert data["services"][0]["service_name"] == "Haircut"


async def test_stats_revenue_calculation(test_client, test_db, sample_tenant):
    """Revenue is calculated from price_cents on confirmed bookings."""
    # Create a paid service
    cursor = await test_db.execute(
        "INSERT INTO services (tenant_id, name, duration_min, capacity, price_cents)"
        " VALUES (?, ?, ?, ?, ?)",
        (sample_tenant["id"], "Deluxe Cut", 90, 2, 49900),
    )
    await test_db.commit()
    svc_id = cursor.lastrowid

    # Create slot
    cursor = await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity) VALUES (?, ?, ?, ?)",
        (svc_id, "2099-06-01T09:00:00", "2099-06-01T10:30:00", 2),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid

    # Book it
    resp = await test_client.post(
        "/api/bookings",
        json={
            "slot_id": slot_id,
            "customer_name": "Erik",
            "customer_email": "erik@test.se",
        },
    )
    assert resp.status_code == 201

    resp = await test_client.get(f"/api/tenants/{sample_tenant['slug']}/stats?period=year")
    data = resp.json()
    assert data["total_revenue_cents"] == 49900


async def test_stats_404_unknown_tenant(test_client):
    """Stats returns 404 for unknown tenant slug."""
    resp = await test_client.get("/api/tenants/nonexistent/stats")
    assert resp.status_code == 404
