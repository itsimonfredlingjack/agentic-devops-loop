"""Event schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    slug: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    venue: str | None = None
    start_time: datetime
    end_time: datetime
    capacity: int = Field(default=100, gt=0)


class EventRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int
    title: str
    slug: str
    description: str | None = None
    venue: str | None = None
    start_time: datetime
    end_time: datetime
    status: str
    capacity: int
    created_at: datetime


class EventTransition(BaseModel):
    status: str
