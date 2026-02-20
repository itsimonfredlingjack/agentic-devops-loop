"""Public-facing schemas for the booking page."""

from pydantic import BaseModel


class PublicServiceView(BaseModel):
    """A service visible on the public booking page."""

    id: int
    name: str
    duration_min: int
    capacity: int


class PublicSlotView(BaseModel):
    """An available time slot shown on the public booking page."""

    id: int
    service_id: int
    start_time: str
    end_time: str
    available: int


class PublicTenantView(BaseModel):
    """Combined tenant info returned by the public booking endpoint."""

    name: str
    slug: str
    services: list[PublicServiceView]
    slots_by_service: dict[int, list[PublicSlotView]]
