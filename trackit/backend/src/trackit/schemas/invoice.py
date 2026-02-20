"""Invoice schemas."""

from pydantic import BaseModel


class InvoiceLineItem(BaseModel):
    project_id: int
    project_name: str
    total_minutes: int
    hours: float
    hourly_rate_cents: int
    amount_cents: int


class InvoiceData(BaseModel):
    invoice_number: str
    tenant_slug: str
    year: int
    month: int
    line_items: list[InvoiceLineItem]
    subtotal_cents: int
    tax_amount_cents: int
    total_cents: int
