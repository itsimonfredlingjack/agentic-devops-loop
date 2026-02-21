"""Check-in schemas."""

from datetime import datetime

from pydantic import BaseModel


class CheckInRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ticket_id: int
    checked_in_at: datetime


class CheckInResponse(BaseModel):
    status: str
    ticket_id: int
    attendee_name: str
    attendee_email: str
    tier_name: str
    event_title: str
    checked_in_at: datetime
