"""Invoice service — business logic for invoice generation.

ALL currency math uses integers (cents/ore). No floats for money.
"""

import aiosqlite

from trackit.schemas.invoice import InvoiceData, InvoiceLineItem
from trackit.services.tenant_service import get_tenant_by_slug

TAX_RATE_BPS = 2500  # 25% Swedish VAT in basis points


async def generate_invoice_data(
    db: aiosqlite.Connection, tenant_slug: str, year: int, month: int
) -> InvoiceData:
    """Generate invoice data for a tenant's unbilled time in a given month.

    Fetches only TimeEntry rows where is_billable=1 AND is_invoiced=0.
    All currency calculations use integer arithmetic (cents).

    Raises ValueError if tenant not found.
    """
    tenant = await get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    # Date range for the month: YYYY-MM-01 to YYYY-MM-31 (inclusive)
    date_prefix = f"{year:04d}-{month:02d}"

    rows = await (
        await db.execute(
            """
            SELECT
                p.id AS project_id,
                p.name AS project_name,
                p.hourly_rate_cents,
                SUM(te.duration_minutes) AS total_minutes
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            WHERE p.tenant_id = ?
              AND te.date LIKE ?
              AND te.is_billable = 1
              AND te.is_invoiced = 0
            GROUP BY p.id
            ORDER BY p.name
            """,
            (tenant.id, f"{date_prefix}%"),
        )
    ).fetchall()

    line_items: list[InvoiceLineItem] = []
    subtotal_cents = 0

    for row in rows:
        total_minutes = row["total_minutes"]
        hourly_rate_cents = row["hourly_rate_cents"]
        hours = total_minutes / 60.0

        # Integer math for money: (minutes * rate) / 60, rounded to nearest cent
        amount_cents = round(total_minutes * hourly_rate_cents / 60)

        line_items.append(
            InvoiceLineItem(
                project_id=row["project_id"],
                project_name=row["project_name"],
                total_minutes=total_minutes,
                hours=hours,
                hourly_rate_cents=hourly_rate_cents,
                amount_cents=amount_cents,
            )
        )
        subtotal_cents += amount_cents

    # Tax: 25% VAT (integer math with basis points)
    tax_amount_cents = round(subtotal_cents * TAX_RATE_BPS / 10000)
    total_cents = subtotal_cents + tax_amount_cents

    invoice_number = f"INV-{tenant_slug.upper()}-{year}{month:02d}"

    return InvoiceData(
        invoice_number=invoice_number,
        tenant_slug=tenant_slug,
        year=year,
        month=month,
        line_items=line_items,
        subtotal_cents=subtotal_cents,
        tax_amount_cents=tax_amount_cents,
        total_cents=total_cents,
    )


async def finalize_invoice(
    db: aiosqlite.Connection, tenant_slug: str, year: int, month: int
) -> int:
    """Mark all billable, uninvoiced time entries for the month as invoiced.

    Runs in a single transaction (commit/rollback) to prevent corruption.
    Returns the number of rows updated.

    Raises ValueError if tenant not found.
    """
    tenant = await get_tenant_by_slug(db, tenant_slug)
    if tenant is None:
        raise ValueError(f"Tenant '{tenant_slug}' not found")

    date_prefix = f"{year:04d}-{month:02d}"

    try:
        cursor = await db.execute(
            """
            UPDATE time_entries
            SET is_invoiced = 1
            WHERE project_id IN (SELECT id FROM projects WHERE tenant_id = ?)
              AND date LIKE ?
              AND is_billable = 1
              AND is_invoiced = 0
            """,
            (tenant.id, f"{date_prefix}%"),
        )
        await db.commit()
        return cursor.rowcount
    except Exception:
        await db.rollback()
        raise
