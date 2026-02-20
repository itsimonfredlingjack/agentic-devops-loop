"""Tests for invoice service — math, tax, finalize flow."""

import pytest

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────


async def _seed_time(test_db, project_id, date, minutes, is_billable=True):
    """Insert a time entry directly into the DB."""
    await test_db.execute(
        """INSERT INTO time_entries (project_id, date, duration_minutes, is_billable)
           VALUES (?, ?, ?, ?)""",
        (project_id, date, minutes, int(is_billable)),
    )
    await test_db.commit()


# ────────────────────────────────────────────────
# Invoice generation
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invoice_basic_calculation(test_db, sample_tenant, sample_project):
    """2h at 1500 SEK/h = 300000 ore subtotal, 75000 tax, 375000 total."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 120)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert len(inv.line_items) == 1
    assert inv.line_items[0].total_minutes == 120
    assert inv.line_items[0].hours == 2.0
    assert inv.line_items[0].amount_cents == 300000
    assert inv.subtotal_cents == 300000
    assert inv.tax_amount_cents == 75000  # 25% VAT
    assert inv.total_cents == 375000


@pytest.mark.asyncio
async def test_invoice_number_format(test_db, sample_tenant, sample_project):
    """Invoice number follows INV-{SLUG}-{YYYYMM} pattern."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-06-15", 60)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 6)
    assert inv.invoice_number == "INV-ACME-CONSULTING-202506"


@pytest.mark.asyncio
async def test_invoice_excludes_non_billable(test_db, sample_tenant, sample_project):
    """Non-billable time entries are excluded from the invoice."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60, is_billable=True)
    await _seed_time(test_db, sample_project["id"], "2025-03-11", 120, is_billable=False)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert inv.line_items[0].total_minutes == 60  # only the billable entry


@pytest.mark.asyncio
async def test_invoice_excludes_already_invoiced(test_db, sample_tenant, sample_project):
    """Already-invoiced entries are not included."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60)
    # Manually mark as invoiced
    await test_db.execute("UPDATE time_entries SET is_invoiced = 1")
    await test_db.commit()

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert len(inv.line_items) == 0
    assert inv.subtotal_cents == 0


@pytest.mark.asyncio
async def test_invoice_filters_by_month(test_db, sample_tenant, sample_project):
    """Only entries in the requested month are included."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60)
    await _seed_time(test_db, sample_project["id"], "2025-04-10", 90)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert inv.line_items[0].total_minutes == 60

    inv_april = await generate_invoice_data(test_db, "acme-consulting", 2025, 4)
    assert inv_april.line_items[0].total_minutes == 90


@pytest.mark.asyncio
async def test_invoice_empty_month(test_db, sample_tenant):
    """Invoice for a month with no entries returns zero totals."""
    from trackit.services.invoice_service import generate_invoice_data

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 1)
    assert inv.line_items == []
    assert inv.subtotal_cents == 0
    assert inv.tax_amount_cents == 0
    assert inv.total_cents == 0


@pytest.mark.asyncio
async def test_invoice_tenant_not_found(test_db):
    """generate_invoice_data raises ValueError for unknown tenant."""
    from trackit.services.invoice_service import generate_invoice_data

    with pytest.raises(ValueError, match="not found"):
        await generate_invoice_data(test_db, "ghost", 2025, 3)


@pytest.mark.asyncio
async def test_invoice_multiple_projects(test_db, sample_tenant):
    """Invoice includes separate line items per project."""
    from trackit.services.invoice_service import generate_invoice_data

    # Create two projects
    cursor = await test_db.execute(
        "INSERT INTO projects (tenant_id, name, hourly_rate_cents) VALUES (?, ?, ?)",
        (sample_tenant["id"], "Project A", 100000),
    )
    await test_db.commit()
    pid_a = cursor.lastrowid

    cursor = await test_db.execute(
        "INSERT INTO projects (tenant_id, name, hourly_rate_cents) VALUES (?, ?, ?)",
        (sample_tenant["id"], "Project B", 200000),
    )
    await test_db.commit()
    pid_b = cursor.lastrowid

    await _seed_time(test_db, pid_a, "2025-05-10", 60)  # 1h @ 1000 SEK = 100000
    await _seed_time(test_db, pid_b, "2025-05-10", 120)  # 2h @ 2000 SEK = 400000

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 5)
    assert len(inv.line_items) == 2
    assert inv.subtotal_cents == 500000  # 100000 + 400000
    assert inv.tax_amount_cents == 125000  # 25%
    assert inv.total_cents == 625000


# ────────────────────────────────────────────────
# Integer math edge cases
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invoice_30min_rounding(test_db, sample_tenant, sample_project):
    """30 minutes at 150000 ore/h = 75000 ore (exact half-hour, no rounding issue)."""
    from trackit.services.invoice_service import generate_invoice_data

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 30)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert inv.line_items[0].amount_cents == 75000


@pytest.mark.asyncio
async def test_invoice_odd_minutes(test_db, sample_tenant):
    """7 minutes at 100000 ore/h = round(7 * 100000 / 60) = 11667 ore."""
    from trackit.services.invoice_service import generate_invoice_data

    cursor = await test_db.execute(
        "INSERT INTO projects (tenant_id, name, hourly_rate_cents) VALUES (?, ?, ?)",
        (sample_tenant["id"], "Odd", 100000),
    )
    await test_db.commit()
    pid = cursor.lastrowid

    await _seed_time(test_db, pid, "2025-03-10", 7)

    inv = await generate_invoice_data(test_db, "acme-consulting", 2025, 3)
    assert inv.line_items[0].amount_cents == round(7 * 100000 / 60)


# ────────────────────────────────────────────────
# Finalize flow
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_finalize_marks_entries_invoiced(test_db, sample_tenant, sample_project):
    """finalize_invoice sets is_invoiced=1 on matching entries."""
    from trackit.services.invoice_service import finalize_invoice

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60)
    await _seed_time(test_db, sample_project["id"], "2025-03-20", 90)

    count = await finalize_invoice(test_db, "acme-consulting", 2025, 3)
    assert count == 2

    # Verify entries are now marked
    rows = await (await test_db.execute("SELECT is_invoiced FROM time_entries")).fetchall()
    for row in rows:
        assert row["is_invoiced"] == 1


@pytest.mark.asyncio
async def test_finalize_is_idempotent(test_db, sample_tenant, sample_project):
    """Second finalize for same month returns 0 (already finalized)."""
    from trackit.services.invoice_service import finalize_invoice

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60)

    count1 = await finalize_invoice(test_db, "acme-consulting", 2025, 3)
    assert count1 == 1

    count2 = await finalize_invoice(test_db, "acme-consulting", 2025, 3)
    assert count2 == 0


@pytest.mark.asyncio
async def test_finalize_does_not_touch_other_months(test_db, sample_tenant, sample_project):
    """Finalize for March does not affect April entries."""
    from trackit.services.invoice_service import finalize_invoice

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60)
    await _seed_time(test_db, sample_project["id"], "2025-04-10", 60)

    await finalize_invoice(test_db, "acme-consulting", 2025, 3)

    # April entry should still be uninvoiced
    row = await (
        await test_db.execute("SELECT is_invoiced FROM time_entries WHERE date LIKE '2025-04%'")
    ).fetchone()
    assert row["is_invoiced"] == 0


@pytest.mark.asyncio
async def test_finalize_skips_non_billable(test_db, sample_tenant, sample_project):
    """Finalize does not mark non-billable entries as invoiced."""
    from trackit.services.invoice_service import finalize_invoice

    await _seed_time(test_db, sample_project["id"], "2025-03-10", 60, is_billable=True)
    await _seed_time(test_db, sample_project["id"], "2025-03-11", 60, is_billable=False)

    count = await finalize_invoice(test_db, "acme-consulting", 2025, 3)
    assert count == 1  # Only the billable one


@pytest.mark.asyncio
async def test_finalize_tenant_not_found(test_db):
    """finalize_invoice raises ValueError for unknown tenant."""
    from trackit.services.invoice_service import finalize_invoice

    with pytest.raises(ValueError, match="not found"):
        await finalize_invoice(test_db, "ghost", 2025, 3)
