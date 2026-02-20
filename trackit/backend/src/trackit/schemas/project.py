"""Project schemas."""

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    hourly_rate_cents: int = Field(..., gt=0, description="Hourly rate in cents/ore")


class ProjectRead(BaseModel):
    id: int
    tenant_id: int
    name: str
    hourly_rate_cents: int
    created_at: str
