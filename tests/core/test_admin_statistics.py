"""Tests for admin statistics and analytics endpoints."""

import pytest
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture
def client() -> FlaskClient:
    """Create a test client for the Flask application.

    Returns:
        FlaskClient: Test client instance.
    """
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.test_client() as client:
        yield client


def login_admin(client: FlaskClient) -> str:
    """Login as admin and return the token.

    Args:
        client: Flask test client.

    Returns:
        str: Authentication token.
    """
    response = client.post(
        "/admin/login", json={"username": "admin", "password": "admin123"}
    )
    data = response.get_json()
    return data.get("token", "")


class TestAdminStatistics:
    """Tests for statistics endpoint."""

    def test_statistics_endpoint_exists(self, client: FlaskClient) -> None:
        """Test that the statistics endpoint exists."""
        token = login_admin(client)
        response = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code != 404

    def test_statistics_requires_auth(self, client: FlaskClient) -> None:
        """Test that statistics requires authentication."""
        response = client.get("/admin/statistics")
        assert response.status_code in (401, 302, 403)

    def test_statistics_returns_json(self, client: FlaskClient) -> None:
        """Test that statistics returns JSON."""
        token = login_admin(client)
        response = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_statistics_contains_subscriber_count(self, client: FlaskClient) -> None:
        """Test that statistics contains subscriber count."""
        token = login_admin(client)
        response = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.get_json()
        assert "total_subscribers" in data

    def test_statistics_contains_active_count(self, client: FlaskClient) -> None:
        """Test that statistics contains active subscriber count."""
        token = login_admin(client)
        response = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.get_json()
        assert "active_subscribers" in data

    def test_statistics_reflects_subscriber_changes(self, client: FlaskClient) -> None:
        """Test that statistics updates when subscribers change."""
        token = login_admin(client)

        # Get initial stats
        response1 = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        initial_count = response1.get_json()["total_subscribers"]

        # Create a subscriber
        client.post(
            "/admin/subscribers",
            json={
                "email": "stats@example.com",
                "name": "Stats Test",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Get updated stats
        response2 = client.get(
            "/admin/statistics", headers={"Authorization": f"Bearer {token}"}
        )
        updated_count = response2.get_json()["total_subscribers"]

        # Verify count increased
        assert updated_count > initial_count


class TestDashboardWithStatistics:
    """Tests for dashboard integration with statistics."""

    def test_dashboard_includes_statistics(self, client: FlaskClient) -> None:
        """Test that dashboard includes statistics."""
        token = login_admin(client)

        # Add a subscriber
        client.post(
            "/admin/subscribers",
            json={
                "email": "dash@example.com",
                "name": "Dashboard Test",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Get dashboard
        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()
        assert "statistics" in data

    def test_dashboard_statistics_accurate(self, client: FlaskClient) -> None:
        """Test that dashboard statistics are accurate."""
        token = login_admin(client)

        # Add subscribers
        for i in range(3):
            client.post(
                "/admin/subscribers",
                json={
                    "email": f"user{i}@example.com",
                    "name": f"User {i}",
                    "subscribed_date": "2026-01-27",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        # Get dashboard
        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()
        stats = data.get("statistics", {})

        # Verify counts
        assert stats.get("total_subscribers") >= 3
        assert stats.get("active_subscribers") >= 3
