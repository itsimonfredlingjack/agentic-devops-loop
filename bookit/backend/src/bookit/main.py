"""BookIt FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.bookit.config import settings
from src.bookit.database import init_db
from src.bookit.routers import bookings, public, services, slots, tenants


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Initialises the database schema on startup.  No teardown is needed for
    SQLite connections because each request opens and closes its own
    connection via the dependency.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to FastAPI while the application is running.
    """
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
app.include_router(tenants.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(slots.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(public.router, prefix="/api")


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A simple status dict.
    """
    return {"status": "ok"}
