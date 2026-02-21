"""Orders router -- order placement and status management."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.database import get_db
from storeit.schemas.order import OrderCreate, OrderRead, OrderTransition
from storeit.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("", response_model=OrderRead, status_code=201)
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = _db_dep,
) -> OrderRead:
    try:
        return await order_service.create_order(session, payload)
    except ValueError as e:
        status = 409 if "Insufficient stock" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e


@router.get("", response_model=list[OrderRead])
async def list_orders(
    email: str | None = Query(default=None),
    session: AsyncSession = _db_dep,
) -> list[OrderRead]:
    return await order_service.list_orders(session, customer_email=email)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = _db_dep,
) -> OrderRead:
    result = await order_service.get_order(session, order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.patch("/{order_id}/status", response_model=OrderRead)
async def transition_order(
    order_id: int,
    payload: OrderTransition,
    session: AsyncSession = _db_dep,
) -> OrderRead:
    try:
        return await order_service.transition_order(session, order_id, payload.status)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e)) from e
