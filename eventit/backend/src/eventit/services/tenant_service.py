"""Tenant service — organizer CRUD."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eventit.models.tenant import Tenant
from eventit.schemas.tenant import TenantCreate, TenantRead


async def create_tenant(session: AsyncSession, payload: TenantCreate) -> TenantRead:
    existing = await session.execute(select(Tenant).where(Tenant.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Tenant slug '{payload.slug}' already exists")

    tenant = Tenant(slug=payload.slug, name=payload.name)
    session.add(tenant)
    await session.flush()
    return TenantRead.model_validate(tenant)


async def get_tenant_by_slug(session: AsyncSession, slug: str) -> TenantRead | None:
    result = await session.execute(select(Tenant).where(Tenant.slug == slug))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return None
    return TenantRead.model_validate(tenant)
