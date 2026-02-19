"""Pytest configuration and shared fixtures.

Sets up FastAPI app-level singletons that are normally created by the
lifespan handler. This allows tests to use ASGITransport without needing
to trigger the full ASGI lifespan protocol.
"""

import pytest

from src import main as app_module
from src.config import get_settings
from src.main import WebSocketManager
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.status import MonitorService


@pytest.fixture(autouse=True)
def setup_app_singletons():
    """Inject app-level singletons before each test.

    Replaces the lifespan-managed globals with fresh instances so that
    tests using ASGITransport (which does not run ASGI lifespan events)
    can call any endpoint without hitting "App not started" assertions.
    """
    settings = get_settings()
    ws = WebSocketManager()
    monitor = MonitorService()

    async def _noop_broadcast(state):  # noqa: ANN001
        pass

    orchestrator = PipelineOrchestrator(
        settings=settings,
        monitor=monitor,
        broadcast=_noop_broadcast,
    )

    app_module._ws_manager = ws
    app_module._monitor = monitor
    app_module._orchestrator = orchestrator

    yield

    # Reset after each test so state doesn't leak
    app_module._ws_manager = None
    app_module._monitor = None
    app_module._orchestrator = None
    app_module._transcriber = None
    app_module._extractor = None
