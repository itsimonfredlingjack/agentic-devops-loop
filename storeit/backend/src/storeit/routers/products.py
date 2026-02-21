"""Products router -- CRUD for products and variants."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from storeit.database import get_db
from storeit.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductWithVariants,
    VariantCreate,
    VariantRead,
)
from storeit.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = _db_dep,
) -> ProductRead:
    try:
        return await product_service.create_product(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("", response_model=list[ProductRead])
async def list_products(
    session: AsyncSession = _db_dep,
) -> list[ProductRead]:
    return await product_service.list_products(session)


@router.get("/{product_id}", response_model=ProductWithVariants)
async def get_product(
    product_id: int,
    session: AsyncSession = _db_dep,
) -> ProductWithVariants:
    result = await product_service.get_product(session, product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@router.post("/{product_id}/variants", response_model=VariantRead, status_code=201)
async def create_variant(
    product_id: int,
    payload: VariantCreate,
    session: AsyncSession = _db_dep,
) -> VariantRead:
    try:
        return await product_service.create_variant(session, product_id, payload)
    except ValueError as e:
        status = 404 if "not found" in str(e) else 409
        raise HTTPException(status_code=status, detail=str(e)) from e
