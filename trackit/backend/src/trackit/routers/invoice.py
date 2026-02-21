"""Invoice router."""

from collections.abc import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from trackit.database import get_db
from trackit.schemas.invoice import InvoiceData
from trackit.services import invoice_service

router = APIRouter(prefix="/tenants/{slug}/invoice", tags=["invoice"])


async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with get_db() as db:
        yield db


_db_dep = Depends(get_db_dep)


@router.get("", response_model=InvoiceData)
async def get_invoice(
    slug: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: aiosqlite.Connection = _db_dep,
) -> InvoiceData:
    try:
        return await invoice_service.generate_invoice_data(db, slug, year, month)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/finalize")
async def finalize_invoice(
    slug: str,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: aiosqlite.Connection = _db_dep,
) -> dict[str, str | int]:
    try:
        count = await invoice_service.finalize_invoice(db, slug, year, month)
        return {"status": "finalized", "entries_locked": count}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
