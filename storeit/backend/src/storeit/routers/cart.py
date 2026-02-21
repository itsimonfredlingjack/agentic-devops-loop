"""Cart router -- session-based shopping cart."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.database import get_db
from storeit.schemas.cart import CartItemAdd, CartItemUpdate, CartRead
from storeit.services import cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.get("/{session_id}", response_model=CartRead)
async def get_cart(
    session_id: str,
    session: AsyncSession = _db_dep,
) -> CartRead:
    result = await cart_service.get_cart(session, session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    return result


@router.post("/{session_id}/items", response_model=CartRead, status_code=201)
async def add_item(
    session_id: str,
    payload: CartItemAdd,
    session: AsyncSession = _db_dep,
) -> CartRead:
    try:
        return await cart_service.add_item(session, session_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{session_id}/items/{item_id}", response_model=CartRead)
async def update_item(
    session_id: str,
    item_id: int,
    payload: CartItemUpdate,
    session: AsyncSession = _db_dep,
) -> CartRead:
    try:
        return await cart_service.update_item(session, session_id, item_id, payload.quantity)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{session_id}/items/{item_id}", response_model=CartRead)
async def remove_item(
    session_id: str,
    item_id: int,
    session: AsyncSession = _db_dep,
) -> CartRead:
    try:
        return await cart_service.remove_item(session, session_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
