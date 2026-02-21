"""Inventory router -- stock management."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.database import get_db
from storeit.schemas.inventory import StockRead, StockUpdate
from storeit.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.get("/{variant_id}", response_model=StockRead)
async def get_stock(
    variant_id: int,
    session: AsyncSession = _db_dep,
) -> StockRead:
    result = await inventory_service.get_stock(session, variant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No inventory for this variant")
    return result


@router.put("/{variant_id}", response_model=StockRead)
async def set_stock(
    variant_id: int,
    payload: StockUpdate,
    session: AsyncSession = _db_dep,
) -> StockRead:
    return await inventory_service.set_stock(session, variant_id, payload.quantity_on_hand)
