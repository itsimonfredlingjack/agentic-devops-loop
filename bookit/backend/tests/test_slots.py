"""Unit tests for slot_service business logic."""

from datetime import date, datetime

import pytest
from fastapi import HTTPException

from src.bookit.schemas.slot import SlotBulkCreate
from src.bookit.services import slot_service

# ────────────────────────────────────────────────
# create_slot
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_slot(test_db, sample_service):
    """Happy path — slot is inserted and returned correctly."""
    start = datetime(2099, 9, 1, 9, 0, 0)
    end = datetime(2099, 9, 1, 10, 0, 0)

    slot = await slot_service.create_slot(test_db, sample_service["id"], start, end, capacity=3)

    assert slot.id is not None
    assert slot.service_id == sample_service["id"]
    assert slot.capacity == 3
    assert slot.booked_count == 0
    assert slot.available is True


@pytest.mark.asyncio
async def test_slot_overlap_prevention(test_db, sample_service):
    """409 when a new slot overlaps an existing one."""
    start = datetime(2099, 9, 2, 9, 0, 0)
    end = datetime(2099, 9, 2, 10, 0, 0)
    await slot_service.create_slot(test_db, sample_service["id"], start, end)

    # Overlapping slot (30-min overlap)
    overlap_start = datetime(2099, 9, 2, 9, 30, 0)
    overlap_end = datetime(2099, 9, 2, 10, 30, 0)

    with pytest.raises(HTTPException) as exc_info:
        await slot_service.create_slot(test_db, sample_service["id"], overlap_start, overlap_end)

    assert exc_info.value.status_code == 409


# ────────────────────────────────────────────────
# generate_slots
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_slots_for_day(test_db, sample_service):
    """Bulk generation produces the correct number of hour-long slots."""
    bulk = SlotBulkCreate(
        date=date(2099, 10, 1),
        start_hour=9,
        end_hour=12,
        interval_min=60,
        capacity=2,
    )
    slots = await slot_service.generate_slots(test_db, sample_service["id"], bulk)

    # 9-10, 10-11, 11-12  → 3 slots
    assert len(slots) == 3
    assert all(s.capacity == 2 for s in slots)
    assert all(s.available for s in slots)
    # Verify ordering
    assert slots[0].start_time < slots[1].start_time < slots[2].start_time


@pytest.mark.asyncio
async def test_generate_slots_skips_overlapping(test_db, sample_service):
    """Bulk generation skips slots that overlap pre-existing ones."""
    # Create a slot at 10:00-11:00 first
    await slot_service.create_slot(
        test_db,
        sample_service["id"],
        datetime(2099, 11, 1, 10, 0, 0),
        datetime(2099, 11, 1, 11, 0, 0),
    )

    bulk = SlotBulkCreate(
        date=date(2099, 11, 1),
        start_hour=9,
        end_hour=12,
        interval_min=60,
        capacity=1,
    )
    slots = await slot_service.generate_slots(test_db, sample_service["id"], bulk)

    # 10-11 should be skipped → only 9-10 and 11-12 created
    assert len(slots) == 2
    start_times = [s.start_time for s in slots]
    assert any("09:00" in t for t in start_times)
    assert any("11:00" in t for t in start_times)


# ────────────────────────────────────────────────
# get_available_slots
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_available_slots_excludes_full(test_db, sample_service):
    """Fully booked slots are not returned by get_available_slots."""
    # Full slot (capacity=1, booked_count=1)
    await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (sample_service["id"], "2099-12-01T09:00:00", "2099-12-01T10:00:00", 1, 1),
    )
    # Available slot (capacity=2, booked_count=1)
    await test_db.execute(
        "INSERT INTO slots (service_id, start_time, end_time, capacity, booked_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (sample_service["id"], "2099-12-01T10:00:00", "2099-12-01T11:00:00", 2, 1),
    )
    await test_db.commit()

    slots = await slot_service.get_available_slots(test_db, sample_service["id"], "2099-12-01")
    assert len(slots) == 1
    assert slots[0].available is True
    assert "10:00" in slots[0].start_time
