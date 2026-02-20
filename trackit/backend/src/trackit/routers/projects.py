"""Project and time entry routers."""

from collections.abc import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from trackit.database import get_db
from trackit.schemas.project import ProjectCreate, ProjectRead
from trackit.schemas.time_entry import TimeEntryCreate, TimeEntryRead
from trackit.services import project_service, time_service

router = APIRouter(prefix="/tenants/{slug}/projects", tags=["projects"])


async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    async with get_db() as db:
        yield db


_db_dep = Depends(get_db_dep)


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    slug: str,
    payload: ProjectCreate,
    db: aiosqlite.Connection = _db_dep,
) -> ProjectRead:
    try:
        return await project_service.create_project(db, slug, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    slug: str,
    db: aiosqlite.Connection = _db_dep,
) -> list[ProjectRead]:
    try:
        return await project_service.list_projects(db, slug)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{project_id}/time", response_model=TimeEntryRead, status_code=201)
async def log_time(
    slug: str,
    project_id: int,
    payload: TimeEntryCreate,
    db: aiosqlite.Connection = _db_dep,
) -> TimeEntryRead:
    # Verify tenant exists
    from trackit.services.tenant_service import get_tenant_by_slug

    tenant = await get_tenant_by_slug(db, slug)
    if tenant is None:
        raise HTTPException(status_code=404, detail=f"Tenant '{slug}' not found")

    try:
        return await time_service.log_time(db, project_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
