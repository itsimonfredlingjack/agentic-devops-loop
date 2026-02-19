"""Pydantic v2 schemas for the Booking resource."""

from enum import StrEnum

from pydantic import BaseModel, Field


class BookingStatus(StrEnum):
    """Allowed booking lifecycle states."""

    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingCreate(BaseModel):
    """Payload for creating a new booking."""

    slot_id: int = Field(..., ge=1, examples=[1])
    customer_name: str = Field(..., min_length=1, max_length=200, examples=["Jane Doe"])
    customer_email: str = Field(..., examples=["jane@example.com"])

    model_config = {"from_attributes": True}


class BookingRead(BaseModel):
    """Booking representation returned by the API."""

    id: int
    slot_id: int
    customer_name: str
    customer_email: str
    status: BookingStatus
    created_at: str

    model_config = {"from_attributes": True}
