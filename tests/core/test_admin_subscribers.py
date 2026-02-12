"""Tests for admin subscriber management endpoints."""

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


class TestAdminSubscribersList:
    """Tests for listing subscribers."""

    def test_subscribers_list_route_exists(self, client: FlaskClient) -> None:
        """Test that the subscribers list endpoint exists."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code != 404

    def test_subscribers_list_requires_auth(self, client: FlaskClient) -> None:
        """Test that subscribers list requires authentication."""
        response = client.get("/admin/subscribers")
        assert response.status_code in (401, 302, 403)

    def test_subscribers_list_returns_json(self, client: FlaskClient) -> None:
        """Test that subscribers list returns JSON."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_subscribers_list_returns_array(self, client: FlaskClient) -> None:
        """Test that subscribers list returns an array."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers", headers={"Authorization": f"Bearer {token}"}
        )
        data = response.get_json()
        assert "subscribers" in data
        assert isinstance(data["subscribers"], list)


class TestAdminSubscriberSearch:
    """Tests for searching subscribers."""

    def test_subscribers_search_route_exists(self, client: FlaskClient) -> None:
        """Test that the search endpoint exists."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/search?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 404

    def test_subscribers_search_requires_auth(self, client: FlaskClient) -> None:
        """Test that search requires authentication."""
        response = client.get("/admin/subscribers/search?q=test")
        assert response.status_code in (401, 302, 403)

    def test_subscribers_search_returns_results(self, client: FlaskClient) -> None:
        """Test that search returns results."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/search?q=test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data


class TestAdminSubscriberExport:
    """Tests for exporting subscribers."""

    def test_subscribers_export_route_exists(self, client: FlaskClient) -> None:
        """Test that the export endpoint exists."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/export", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code != 404

    def test_subscribers_export_requires_auth(self, client: FlaskClient) -> None:
        """Test that export requires authentication."""
        response = client.get("/admin/subscribers/export")
        assert response.status_code in (401, 302, 403)

    def test_subscribers_export_returns_csv(self, client: FlaskClient) -> None:
        """Test that export returns CSV data."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/export", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.content_type or "csv" in response.content_type
