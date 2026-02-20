"""Pydantic v2 schemas for the Service resource."""

from pydantic import BaseModel, Field, field_validator


class ServiceCreate(BaseModel):
    """Payload for creating a new service under a tenant."""

    name: str = Field(..., min_length=1, max_length=200, examples=["Haircut"])
    duration_min: int = Field(default=60, ge=5, le=480, examples=[60])
    capacity: int = Field(default=1, ge=1, le=1000, examples=[1])
    price_cents: int = Field(default=0, ge=0, examples=[0])

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        """Ensure name is not blank after stripping whitespace."""
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class ServiceRead(BaseModel):
    """Service representation returned by the API."""

    id: int
    tenant_id: int
    name: str
    duration_min: int
    capacity: int
    price_cents: int = 0
    created_at: str

    model_config = {"from_attributes": True}
