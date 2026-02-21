"""StoreIt -- Production-grade e-commerce backend."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from storeit.config import settings
from storeit.routers import cart, categories, inventory, orders, payments, products


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Alembic handles schema in production.
    # For dev, use Base.metadata.create_all via a script.
    yield


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
