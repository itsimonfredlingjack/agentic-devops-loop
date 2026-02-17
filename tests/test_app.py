"""Tests for the Flask application."""

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


class TestHelloEndpoint:
    """Tests for the API endpoint."""

    def test_hello_returns_200(self, client: FlaskClient) -> None:
        """Test that the API endpoint returns 200 OK."""
        response = client.get("/api")
        assert response.status_code == 200

    def test_hello_returns_json(self, client: FlaskClient) -> None:
        """Test that the API endpoint returns JSON."""
        response = client.get("/api")
        assert response.content_type == "application/json"

    def test_hello_returns_message(self, client: FlaskClient) -> None:
        """Test that the API endpoint returns expected message."""
        response = client.get("/api")
        data = response.get_json()
        assert "message" in data
        assert data["message"] == "Hello, Agentic Dev Loop!"


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        """Test that the health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client: FlaskClient) -> None:
        """Test that the health endpoint returns JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_returns_healthy_status(self, client: FlaskClient) -> None:
        """Test that the health endpoint returns healthy status."""
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_contains_status(self, client: FlaskClient) -> None:
        """Test that the health endpoint returns status and timestamp."""
        from datetime import datetime

        response = client.get("/health")
        data = response.get_json()

        # Check that both required fields are present
        assert "status" in data
        assert "timestamp" in data

        # Verify status value
        assert data["status"] == "healthy"

        # Verify timestamp is valid ISO-8601 format
        timestamp_str = data["timestamp"]
        try:
            datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            pytest.fail(f"Invalid ISO-8601 timestamp: {timestamp_str}")


class TestVersionEndpoint:
    """Tests for the version endpoint."""

    def test_version_returns_200(self, client: FlaskClient) -> None:
        """Test that the version endpoint returns 200 OK."""
        response = client.get("/version")
        assert response.status_code == 200

    def test_version_returns_json(self, client: FlaskClient) -> None:
        """Test that the version endpoint returns JSON."""
        response = client.get("/version")
        assert response.content_type == "application/json"

    def test_version_reads_git_sha_from_env(
        self, client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the version endpoint reads GIT_SHA from the environment."""
        monkeypatch.setenv("GIT_SHA", "0123456789abcdef")
        response = client.get("/version")
        data = response.get_json()
        assert data["sha"] == "0123456789abcdef"


class TestAppCreation:
    """Tests for app factory function."""

    def test_create_app_returns_flask_instance(self) -> None:
        """Test that create_app returns a Flask instance."""
        from flask import Flask

        app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        assert isinstance(app, Flask)

    def test_create_app_has_routes(self) -> None:
        """Test that created app has expected routes."""
        app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/" in rules
        assert "/api" in rules
        assert "/health" in rules
        assert "/version" in rules
