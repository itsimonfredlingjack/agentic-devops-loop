"""Health endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    """GET /health returns 200 with service name."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "storeit"}
