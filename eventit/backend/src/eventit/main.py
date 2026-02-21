"""EventIt — Multi-tenant event planning and ticketing."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eventit.config import settings
from eventit.database import engine
from eventit.routers import checkin, events, public, tenants, tickets


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="EventIt API",
    version="0.1.0",
    description="Event planning and ticketing with QR check-in",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_all_routers = [tenants, events, public, tickets, checkin]
for _mod in _all_routers:
    app.include_router(_mod.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "eventit"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
