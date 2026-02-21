"""Product, variant, and category schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class CategoryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    description: str | None = None
    created_at: datetime


class VariantCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=300)
    price_cents: int = Field(..., gt=0, description="Price in cents/ore")
    weight_grams: int | None = None


class VariantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    product_id: int
    sku: str
    name: str
    price_cents: int
    weight_grams: int | None = None
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    slug: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    category_id: int | None = None


class ProductRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str
    description: str | None = None
    category_id: int | None = None
    is_active: bool
    created_at: datetime


class ProductWithVariants(ProductRead):
    variants: list[VariantRead] = []
