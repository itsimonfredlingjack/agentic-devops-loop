"""Tenant router."""

from collections.abc import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from trackit.database import get_db
from trackit.schemas.tenant import TenantCreate, TenantRead
from trackit.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with get_db() as db:
        yield db


_db_dep = Depends(get_db_dep)


@router.post("", response_model=TenantRead, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    db: aiosqlite.Connection = _db_dep,
) -> TenantRead:
    return await tenant_service.create_tenant(db, payload)


@router.get("/{slug}", response_model=TenantRead)
async def get_tenant(
    slug: str,
    db: aiosqlite.Connection = _db_dep,
) -> TenantRead:
    tenant = await tenant_service.get_tenant_by_slug(db, slug)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")
    return tenant
