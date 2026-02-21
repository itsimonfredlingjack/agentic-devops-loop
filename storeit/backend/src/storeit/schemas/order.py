"""Order schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    cart_session_id: str
    customer_email: str = Field(..., min_length=1, max_length=320)
    customer_name: str = Field(..., min_length=1, max_length=200)


class OrderItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    variant_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int


class OrderRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    customer_email: str
    customer_name: str
    status: str
    total_cents: int
    created_at: datetime
    items: list[OrderItemRead] = []


class OrderTransition(BaseModel):
    status: str
