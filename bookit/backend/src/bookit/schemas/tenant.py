"""Pydantic v2 schemas for the Tenant resource."""

import re

from pydantic import BaseModel, Field, field_validator


def _slugify(name: str) -> str:
    """Convert a tenant name to a URL-safe slug.

    Args:
        name: The raw tenant name (e.g. ``"Acme Corp"``).

    Returns:
        A lowercase, hyphen-separated slug (e.g. ``"acme-corp"``).
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


class TenantCreate(BaseModel):
    """Payload for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=200, examples=["Acme Barbershop"])

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        """Ensure name is not blank after stripping whitespace."""
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class TenantRead(BaseModel):
    """Tenant representation returned by the API."""

    id: int
    name: str
    slug: str
    created_at: str

    model_config = {"from_attributes": True}
