"""Tests for admin authentication functionality."""

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


class TestAdminLoginEndpoint:
    """Tests for admin login endpoint."""

    def test_admin_login_route_exists(self, client: FlaskClient) -> None:
        """Test that the admin login endpoint exists."""
        response = client.post("/admin/login")
        # Should not return 404
        assert response.status_code != 404

    def test_admin_login_requires_credentials(self, client: FlaskClient) -> None:
        """Test that admin login requires username and password."""
        response = client.post("/admin/login", json={})
        assert response.status_code == 400

    def test_admin_login_with_valid_credentials(self, client: FlaskClient) -> None:
        """Test successful admin login with valid credentials."""
        response = client.post(
            "/admin/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data or "session" in data

    def test_admin_login_with_invalid_credentials(self, client: FlaskClient) -> None:
        """Test admin login rejection with invalid credentials."""
        response = client.post(
            "/admin/login", json={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_admin_login_returns_json(self, client: FlaskClient) -> None:
        """Test that login endpoint returns JSON."""
        response = client.post(
            "/admin/login", json={"username": "admin", "password": "admin123"}
        )
        assert response.content_type == "application/json"


class TestAdminDashboardEndpoint:
    """Tests for admin dashboard endpoint."""

    def test_admin_dashboard_route_exists(self, client: FlaskClient) -> None:
        """Test that the admin dashboard endpoint exists."""
        response = client.get("/admin")
        # Should not return 404
        assert response.status_code != 404

    def test_admin_dashboard_requires_authentication(self, client: FlaskClient) -> None:
        """Test that admin dashboard requires authentication."""
        response = client.get("/admin")
        # Without login, should be 401 or redirected
        assert response.status_code in (401, 302, 403)

    def test_admin_dashboard_with_authentication(self, client: FlaskClient) -> None:
        """Test accessing dashboard after login."""
        token = login_admin(client)
        assert token

        # Access dashboard with token
        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_admin_dashboard_returns_json(self, client: FlaskClient) -> None:
        """Test that dashboard returns JSON data."""
        token = login_admin(client)
        assert token

        response = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            assert response.content_type == "application/json"
            data = response.get_json()
            assert "dashboard" in data
