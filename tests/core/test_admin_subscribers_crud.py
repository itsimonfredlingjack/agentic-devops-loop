"""Tests for admin subscriber CRUD operations."""

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


class TestAdminSubscriberCreate:
    """Tests for creating subscribers."""

    def test_create_subscriber_route_exists(self, client: FlaskClient) -> None:
        """Test that the create subscriber endpoint exists."""
        token = login_admin(client)
        response = client.post(
            "/admin/subscribers",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 404

    def test_create_subscriber_requires_auth(self, client: FlaskClient) -> None:
        """Test that create requires authentication."""
        response = client.post(
            "/admin/subscribers",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "subscribed_date": "2026-01-27",
            },
        )
        assert response.status_code in (401, 302, 403)

    def test_create_subscriber_success(self, client: FlaskClient) -> None:
        """Test successful subscriber creation."""
        token = login_admin(client)
        response = client.post(
            "/admin/subscribers",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"

    def test_create_subscriber_missing_fields(self, client: FlaskClient) -> None:
        """Test subscriber creation with missing fields."""
        token = login_admin(client)
        response = client.post(
            "/admin/subscribers",
            json={"email": "test@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400


class TestAdminSubscriberRead:
    """Tests for reading subscriber details."""

    def test_get_subscriber_route_exists(self, client: FlaskClient) -> None:
        """Test that the get subscriber endpoint exists."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/1", headers={"Authorization": f"Bearer {token}"}
        )
        # Should either return 200 or 404, not refuse to exist
        assert response.status_code != 405

    def test_get_subscriber_requires_auth(self, client: FlaskClient) -> None:
        """Test that get subscriber requires authentication."""
        response = client.get("/admin/subscribers/1")
        assert response.status_code in (401, 302, 403)

    def test_get_nonexistent_subscriber(self, client: FlaskClient) -> None:
        """Test getting a nonexistent subscriber."""
        token = login_admin(client)
        response = client.get(
            "/admin/subscribers/999", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_get_existing_subscriber(self, client: FlaskClient) -> None:
        """Test getting an existing subscriber."""
        token = login_admin(client)

        # Create a subscriber first
        create_response = client.post(
            "/admin/subscribers",
            json={
                "email": "read@example.com",
                "name": "Read Test",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        subscriber_id = create_response.get_json()["id"]

        # Now get it
        response = client.get(
            f"/admin/subscribers/{subscriber_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "read@example.com"


class TestAdminSubscriberUpdate:
    """Tests for updating subscribers."""

    def test_update_subscriber_route_exists(self, client: FlaskClient) -> None:
        """Test that the update subscriber endpoint exists."""
        token = login_admin(client)
        response = client.put(
            "/admin/subscribers/1",
            json={"email": "updated@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should either return 200/404, not refuse to exist
        assert response.status_code != 405

    def test_update_subscriber_requires_auth(self, client: FlaskClient) -> None:
        """Test that update requires authentication."""
        response = client.put(
            "/admin/subscribers/1", json={"email": "updated@example.com"}
        )
        assert response.status_code in (401, 302, 403)

    def test_update_nonexistent_subscriber(self, client: FlaskClient) -> None:
        """Test updating a nonexistent subscriber."""
        token = login_admin(client)
        response = client.put(
            "/admin/subscribers/999",
            json={"email": "updated@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_subscriber_success(self, client: FlaskClient) -> None:
        """Test successful subscriber update."""
        token = login_admin(client)

        # Create a subscriber
        create_response = client.post(
            "/admin/subscribers",
            json={
                "email": "original@example.com",
                "name": "Original Name",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        subscriber_id = create_response.get_json()["id"]

        # Update it
        response = client.put(
            f"/admin/subscribers/{subscriber_id}",
            json={"email": "updated@example.com", "name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "updated@example.com"
        assert data["name"] == "Updated Name"


class TestAdminSubscriberDelete:
    """Tests for deleting subscribers."""

    def test_delete_subscriber_route_exists(self, client: FlaskClient) -> None:
        """Test that the delete subscriber endpoint exists."""
        token = login_admin(client)
        response = client.delete(
            "/admin/subscribers/1", headers={"Authorization": f"Bearer {token}"}
        )
        # Should either return 200/204/404, not refuse to exist
        assert response.status_code != 405

    def test_delete_subscriber_requires_auth(self, client: FlaskClient) -> None:
        """Test that delete requires authentication."""
        response = client.delete("/admin/subscribers/1")
        assert response.status_code in (401, 302, 403)

    def test_delete_nonexistent_subscriber(self, client: FlaskClient) -> None:
        """Test deleting a nonexistent subscriber."""
        token = login_admin(client)
        response = client.delete(
            "/admin/subscribers/999", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_delete_subscriber_success(self, client: FlaskClient) -> None:
        """Test successful subscriber deletion."""
        token = login_admin(client)

        # Create a subscriber
        create_response = client.post(
            "/admin/subscribers",
            json={
                "email": "delete@example.com",
                "name": "Delete Test",
                "subscribed_date": "2026-01-27",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        subscriber_id = create_response.get_json()["id"]

        # Delete it
        response = client.delete(
            f"/admin/subscribers/{subscriber_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in (200, 204)

        # Verify it's gone
        get_response = client.get(
            f"/admin/subscribers/{subscriber_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404
