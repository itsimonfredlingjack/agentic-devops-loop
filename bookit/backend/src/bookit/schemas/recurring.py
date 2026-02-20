"""Pydantic v2 schemas for recurring booking rules."""

from enum import StrEnum

from pydantic import BaseModel, Field


class RecurringFrequency(StrEnum):
    """Supported recurrence intervals."""

    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class RecurringCreate(BaseModel):
    """Payload for creating a recurring booking series."""

    slot_id: int = Field(..., ge=1)
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: str
    customer_phone: str | None = None
    frequency: RecurringFrequency = RecurringFrequency.weekly
    occurrences: int = Field(default=4, ge=2, le=52)

    model_config = {"from_attributes": True}


class RecurringRead(BaseModel):
    """Representation of a recurring rule with its booking IDs."""

    id: int
    frequency: RecurringFrequency
    occurrences: int
    booking_ids: list[int]
    created_at: str

    model_config = {"from_attributes": True}
