"""Pydantic v2 schemas for statistics responses."""

from pydantic import BaseModel


class ServiceStats(BaseModel):
    """Booking stats per service."""

    service_id: int
    service_name: str
    booking_count: int
    revenue_cents: int


class StatsResponse(BaseModel):
    """Aggregated statistics for a tenant."""

    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    total_revenue_cents: int
    services: list[ServiceStats]
    period: str
