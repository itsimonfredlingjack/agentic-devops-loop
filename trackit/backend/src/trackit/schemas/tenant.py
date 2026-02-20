"""Tenant schemas."""

from pydantic import BaseModel, Field, field_validator


class TenantCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("slug")
    @classmethod
    def slug_must_be_lowercase(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "-")


class TenantRead(BaseModel):
    id: int
    slug: str
    name: str
    created_at: str
