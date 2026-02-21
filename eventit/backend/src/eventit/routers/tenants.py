"""Tenant router."""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.database import get_db
from eventit.schemas.tenant import TenantCreate, TenantRead
from eventit.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


_db_dep = Depends(get_db_dep)


@router.post("", response_model=TenantRead, status_code=201)
async def create_tenant(payload: TenantCreate, session: AsyncSession = _db_dep) -> TenantRead:
    try:
        return await tenant_service.create_tenant(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/{slug}", response_model=TenantRead)
async def get_tenant(slug: str, session: AsyncSession = _db_dep) -> TenantRead:
    result = await tenant_service.get_tenant_by_slug(session, slug)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    return result
