"""Pydantic v2 schemas for the Slot resource."""

import datetime as dt

from pydantic import BaseModel, Field, computed_field, model_validator


class SlotCreate(BaseModel):
    """Payload for creating a single slot."""

    start_time: dt.datetime = Field(..., examples=["2026-03-01T09:00:00"])
    end_time: dt.datetime = Field(..., examples=["2026-03-01T10:00:00"])
    capacity: int = Field(default=1, ge=1, le=1000, examples=[1])

    @model_validator(mode="after")
    def end_after_start(self) -> "SlotCreate":
        """Validate that end_time is strictly after start_time."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SlotRead(BaseModel):
    """Slot representation returned by the API."""

    id: int
    service_id: int
    start_time: str
    end_time: str
    capacity: int
    booked_count: int
    created_at: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def available(self) -> bool:
        """True when there is remaining booking capacity."""
        return self.booked_count < self.capacity

    model_config = {"from_attributes": True}


class SlotBulkCreate(BaseModel):
    """Payload for bulk-generating slots for a full day."""

    date: dt.date = Field(..., examples=["2026-03-01"])
    start_hour: int = Field(default=8, ge=0, le=23, examples=[8])
    end_hour: int = Field(default=17, ge=1, le=24, examples=[17])
    interval_min: int = Field(default=60, ge=5, le=480, examples=[60])
    capacity: int = Field(default=1, ge=1, le=1000, examples=[1])

    @model_validator(mode="after")
    def end_after_start(self) -> "SlotBulkCreate":
        """Validate that end_hour is strictly after start_hour."""
        if self.end_hour <= self.start_hour:
            raise ValueError("end_hour must be greater than start_hour")
        return self
