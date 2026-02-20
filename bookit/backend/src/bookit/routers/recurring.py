"""Recurring bookings router."""

import aiosqlite
from fastapi import APIRouter, Depends

from src.bookit.database import get_db
from src.bookit.schemas.recurring import RecurringCreate, RecurringRead
from src.bookit.services.recurring_service import (
    cancel_recurring_series,
    create_recurring_booking,
    get_recurring_rule,
)

router = APIRouter(tags=["recurring"])


async def get_db_dep() -> aiosqlite.Connection:
    """FastAPI dependency that yields a DB connection."""
    async with get_db() as db:
        yield db


@router.post("/bookings/recurring", response_model=RecurringRead, status_code=201)
async def create_recurring(
    payload: RecurringCreate,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> RecurringRead:
    """Create a recurring booking series."""
    return await create_recurring_booking(db, payload)


@router.get("/bookings/recurring/{rule_id}", response_model=RecurringRead)
async def get_recurring(
    rule_id: int,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> RecurringRead:
    """Get a recurring rule with its bookings."""
    return await get_recurring_rule(db, rule_id)


@router.delete("/bookings/recurring/{rule_id}")
async def delete_recurring(
    rule_id: int,
    db: aiosqlite.Connection = Depends(get_db_dep),
) -> dict[str, int]:
    """Cancel all confirmed bookings in a recurring series."""
    count = await cancel_recurring_series(db, rule_id)
    return {"cancelled": count}
