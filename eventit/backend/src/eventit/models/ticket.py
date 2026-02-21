"""Ticket tier and ticket models."""

from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eventit.models.base import Base, TimestampMixin


class TicketStatus(StrEnum):
    confirmed = "confirmed"
    checked_in = "checked_in"
    cancelled = "cancelled"


class TicketTier(TimestampMixin, Base):
    """A pricing tier for an event (e.g. VIP, General, Early Bird)."""

    __tablename__ = "ticket_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    sold_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    event: Mapped["Event"] = relationship(back_populates="tiers")  # noqa: F821
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="tier")


class Ticket(TimestampMixin, Base):
    """An individual ticket purchased by an attendee."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tier_id: Mapped[int] = mapped_column(ForeignKey("ticket_tiers.id"), nullable=False)
    attendee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    attendee_email: Mapped[str] = mapped_column(String(320), nullable=False)
    qr_code: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    qr_image_b64: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")

    tier: Mapped[TicketTier] = relationship(back_populates="tickets")
