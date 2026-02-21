"""Cart schemas."""

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    variant_id: int
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    variant_id: int
    quantity: int


class CartRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    session_id: str
    items: list[CartItemRead] = []
