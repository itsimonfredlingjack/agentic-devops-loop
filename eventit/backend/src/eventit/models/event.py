"""Event model with state machine."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eventit.models.base import Base, TimestampMixin


class EventStatus(StrEnum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"
    completed = "completed"


EVENT_TRANSITIONS: dict[EventStatus, set[EventStatus]] = {
    EventStatus.draft: {EventStatus.published, EventStatus.cancelled},
    EventStatus.published: {EventStatus.cancelled, EventStatus.completed},
    EventStatus.cancelled: set(),
    EventStatus.completed: set(),
}


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(300), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    tenant: Mapped["Tenant"] = relationship(back_populates="events")  # noqa: F821
    tiers: Mapped[list["TicketTier"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
