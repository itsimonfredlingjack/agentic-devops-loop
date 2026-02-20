"""BookIt FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.bookit.config import settings
from src.bookit.database import init_db
from src.bookit.routers import (
    bookings,
    payments,
    public,
    recurring,
    services,
    slots,
    stats,
    tenants,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    await init_db()
    yield


app = FastAPI(
    title="BookIt API",
    version="0.1.0",
    description="Multi-tenant booking system API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api prefix
_all_routers = [tenants, services, slots, bookings, public, payments, recurring, stats]
for _mod in _all_routers:
    app.include_router(_mod.router, prefix="/api")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
