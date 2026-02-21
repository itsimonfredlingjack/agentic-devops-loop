"""Ticket and tier schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class TierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price_cents: int = Field(..., ge=0)
    capacity: int = Field(..., gt=0)


class TierRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    event_id: int
    name: str
    price_cents: int
    capacity: int
    sold_count: int
    created_at: datetime

    @property
    def available(self) -> int:
        return self.capacity - self.sold_count


class TicketPurchase(BaseModel):
    tier_id: int
    attendee_name: str = Field(..., min_length=1, max_length=200)
    attendee_email: str = Field(..., min_length=1, max_length=320)


class TicketRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tier_id: int
    attendee_name: str
    attendee_email: str
    qr_code: str
    status: str
    created_at: datetime
