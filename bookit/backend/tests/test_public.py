"""Tests for the public booking endpoint."""

from datetime import UTC, datetime, timedelta

import pytest


async def _insert_near_future_slot(test_db, service_id, *, booked_count=0, capacity=2):
    """Insert a slot starting tomorrow (within the 14-day window)."""
    tomorrow = datetime.now(tz=UTC) + timedelta(days=1)
    start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    end = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    cursor = await test_db.execute(
        """
        INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count)
        VALUES (?, ?, ?, ?, ?)
        """,
        (service_id, start, end, capacity, booked_count),
    )
    await test_db.commit()
    slot_id = cursor.lastrowid
    cursor = await test_db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,))
    row = await cursor.fetchone()
    return dict(row)


@pytest.mark.asyncio
async def test_public_endpoint_returns_structure(test_db, test_client, sample_service):
    """Public endpoint returns tenant info with services and slots."""
    slot = await _insert_near_future_slot(test_db, sample_service["id"])

    resp = await test_client.get("/api/book/test-salon")
    assert resp.status_code == 200

    data = resp.json()
    assert data["name"] == "Test Salon"
    assert data["slug"] == "test-salon"
    assert len(data["services"]) == 1
    assert data["services"][0]["name"] == "Haircut"
    assert data["services"][0]["duration_min"] == 60
    assert data["services"][0]["capacity"] == 2

    service_id = str(data["services"][0]["id"])
    assert service_id in data["slots_by_service"]
    slots = data["slots_by_service"][service_id]
    assert len(slots) == 1
    assert slots[0]["start_time"] == slot["start_time"]
    assert slots[0]["available"] == 2


@pytest.mark.asyncio
async def test_public_endpoint_404_unknown_slug(test_client):
    """Unknown slug returns 404."""
    resp = await test_client.get("/api/book/does-not-exist")
    assert resp.status_code == 404
    assert "does-not-exist" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_public_endpoint_excludes_fully_booked(test_db, test_client, sample_service):
    """Fully booked slots are excluded from the response."""
    await _insert_near_future_slot(test_db, sample_service["id"], booked_count=2, capacity=2)

    resp = await test_client.get("/api/book/test-salon")
    assert resp.status_code == 200

    data = resp.json()
    service_id = str(data["services"][0]["id"])
    slots = data["slots_by_service"][service_id]
    assert len(slots) == 0


@pytest.mark.asyncio
async def test_public_endpoint_no_services(test_db, test_client, sample_tenant):
    """Tenant with no services returns empty lists."""
    resp = await test_client.get("/api/book/test-salon")
    assert resp.status_code == 200

    data = resp.json()
    assert data["services"] == []
    assert data["slots_by_service"] == {}
