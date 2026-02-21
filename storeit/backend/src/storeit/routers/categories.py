"""Categories router."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.database import get_db
from storeit.schemas.product import CategoryCreate, CategoryRead
from storeit.services import product_service

router = APIRouter(prefix="/categories", tags=["categories"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = _db_dep,
) -> CategoryRead:
    try:
        return await product_service.create_category(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    session: AsyncSession = _db_dep,
) -> list[CategoryRead]:
    return await product_service.list_categories(session)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    session: AsyncSession = _db_dep,
) -> CategoryRead:
    result = await product_service.get_category(session, category_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return result
