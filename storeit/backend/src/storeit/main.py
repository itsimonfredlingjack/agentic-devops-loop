"""StoreIt -- Production-grade e-commerce backend."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from storeit.config import settings
from storeit.database import async_session_factory, engine
from storeit.routers import cart, categories, inventory, orders, payments, products

logger = logging.getLogger(__name__)


async def _reservation_expiry_loop() -> None:
    """Background task that expires stale reservations every 60 seconds."""
    from storeit.services.inventory_service import expire_stale_reservations

    while True:
        await asyncio.sleep(60)
        try:
            async with async_session_factory() as session:
                count = await expire_stale_reservations(session)
                await session.commit()
                if count > 0:
                    logger.info("Expired %d stale reservation(s)", count)
        except Exception:
            logger.exception("Error expiring reservations")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Start reservation expiry background task
    task = asyncio.create_task(_reservation_expiry_loop())
    logger.info("Reservation expiry loop started (interval=60s)")
    yield
    # Shutdown: cancel background task and dispose engine
    task.cancel()
    await engine.dispose()
    logger.info("StoreIt shutdown complete")


app = FastAPI(
    title="StoreIt API",
    version="0.1.0",
    description="E-commerce backend with PostgreSQL concurrency patterns",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_all_routers = [products, categories, inventory, cart, orders, payments]
for _mod in _all_routers:
    app.include_router(_mod.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "storeit"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
