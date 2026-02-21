"""Inventory schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class StockUpdate(BaseModel):
    quantity_on_hand: int = Field(..., ge=0)


class StockRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    variant_id: int
    quantity_on_hand: int
    quantity_reserved: int

    @property
    def available(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved


class ReservationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    variant_id: int
    quantity: int
    cart_id: str
    expires_at: datetime
    status: str
