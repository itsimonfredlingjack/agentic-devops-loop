"""TimeEntry schemas."""

from pydantic import BaseModel, Field


class TimeEntryCreate(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes, must be > 0")
    is_billable: bool = Field(default=True)


class TimeEntryRead(BaseModel):
    id: int
    project_id: int
    date: str
    duration_minutes: int
    is_billable: bool
    is_invoiced: bool
    created_at: str
