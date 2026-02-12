"""Tests for admin endpoints reading from the SQLAlchemy database.

Verifies that admin endpoints use the same database as the newsflash
subscription flow (GE-49 acceptance criteria).
"""

import pytest
from flask.testing import FlaskClient

from app import create_app
from src.sejfa.newsflash.data.models import Subscriber, db


@pytest.fixture
def app():
    """Create test app with in-memory SQLite database."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    return app


@pytest.fixture
def client(app) -> FlaskClient:
    """Create a test client."""
    with app.test_client() as client:
        yield client


def login_admin(client: FlaskClient) -> str:
    """Login as admin and return the token."""
    response = client.post(
        "/admin/login", json={"username": "admin", "password": "admin123"}
    )
    return response.get_json().get("token", "")


def seed_subscriber_via_db(app, email: str, name: str) -> Subscriber:
    """Insert a subscriber directly into the database (simulating newsflash)."""
    with app.app_context():
        subscriber = Subscriber(email=email, name=name)
        db.session.add(subscriber)
        db.session.commit()
        # Refresh to get generated fields
        db.session.refresh(subscriber)
        return subscriber


class TestAdminReadsFromDatabase:
    """Admin endpoints should read from the SQLAlchemy database."""

    def test_list_shows_db_subscribers(self, app, client: FlaskClient) -> None:
        """GET /admin/subscribers returns subscribers from the database."""
        seed_subscriber_via_db(app, "newsflash@example.com", "NF User")
        token = login_admin(client)

        response = client.get(
            "/admin/subscribers",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        emails = [s["email"] for s in data["subscribers"]]
        assert "newsflash@example.com" in emails

    def test_statistics_counts_db_subscribers(self, app, client: FlaskClient) -> None:
        """GET /admin/statistics shows correct count from database."""
        seed_subscriber_via_db(app, "stat1@example.com", "Stat One")
        seed_subscriber_via_db(app, "stat2@example.com", "Stat Two")
        token = login_admin(client)

        response = client.get(
            "/admin/statistics",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total_subscribers"] >= 2
        assert data["active_subscribers"] >= 2

    def test_search_finds_db_subscribers(self, app, client: FlaskClient) -> None:
        """Search endpoint finds subscribers stored in the database."""
        seed_subscriber_via_db(app, "findme@example.com", "Findable")
        token = login_admin(client)

        response = client.get(
            "/admin/subscribers/search?q=findme",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        emails = [s["email"] for s in data["results"]]
        assert "findme@example.com" in emails

    def test_export_includes_db_subscribers(self, app, client: FlaskClient) -> None:
        """Export CSV includes subscribers stored in the database."""
        seed_subscriber_via_db(app, "export@example.com", "Export User")
        token = login_admin(client)

        response = client.get(
            "/admin/subscribers/export",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "export@example.com" in response.data.decode()

    def test_newsflash_subscriber_visible_in_admin(
        self, app, client: FlaskClient
    ) -> None:
        """Subscribers created via newsflash form should appear in admin API."""
        # Simulate newsflash subscription via the confirm endpoint
        client.post(
            "/subscribe/confirm",
            data={"email": "via-form@example.com", "name": "Form User"},
        )
        token = login_admin(client)

        response = client.get(
            "/admin/subscribers",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.get_json()
        emails = [s["email"] for s in data["subscribers"]]
        assert "via-form@example.com" in emails
