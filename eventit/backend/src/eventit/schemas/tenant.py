"""Tenant schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)


class TenantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    slug: str
    name: str
    created_at: datetime
