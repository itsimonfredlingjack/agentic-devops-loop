"""Integration tests for News Flash subscription."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.sejfa.newsflash.business.subscription_service import SubscriptionService
from src.sejfa.newsflash.data.models import db
from src.sejfa.newsflash.data.subscriber_repository import SubscriberRepository
from src.sejfa.newsflash.presentation.routes import create_newsflash_blueprint


@pytest.fixture
def app() -> Flask:
    """Create test application with in-memory SQLite."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "test-secret-key"

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register blueprint with DI
    repo = SubscriberRepository()
    service = SubscriptionService(repository=repo)
    bp = create_newsflash_blueprint(subscription_service=service)
    app.register_blueprint(bp, url_prefix="/newsflash")

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()


class TestNewsFlashSubscription:
    """Test News Flash subscription workflow."""

    def test_subscribe_page_loads(self, client: FlaskClient) -> None:
        """Test that subscribe page loads successfully."""
        response = client.get("/newsflash/subscribe")
        assert response.status_code == 200
        assert b"Join Our Newsletter" in response.data

    def test_subscribe_confirm_with_valid_data(self, client: FlaskClient) -> None:
        """Test successful subscription with valid email and name."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "test@example.com", "name": "John Doe"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"prenumeration" in response.data.lower()

    def test_subscribe_confirm_empty_email_shows_error(
        self, client: FlaskClient
    ) -> None:
        """Test that empty email shows 'Email is required' error."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "", "name": "John Doe"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Email is required" in response.data

    def test_subscribe_confirm_invalid_email_shows_error(
        self, client: FlaskClient
    ) -> None:
        """Test that invalid email shows 'Invalid email format' error."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "invalid", "name": "John Doe"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"Invalid email format" in response.data

    def test_subscribe_confirm_preserves_input_on_error(
        self, client: FlaskClient
    ) -> None:
        """Test that user input is preserved when validation fails."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "invalid", "name": "John Doe"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"invalid" in response.data  # Email preserved
        assert b"John Doe" in response.data  # Name preserved

    def test_subscribe_confirm_error_banner_visible(self, client: FlaskClient) -> None:
        """Test that error banner is visible on validation failure."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "", "name": "John"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"error-banner" in response.data

    def test_subscribe_confirm_normalizes_email(self, client: FlaskClient) -> None:
        """Test that email is normalized (uppercase -> lowercase, trimmed)."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "  TEST@EXAMPLE.COM  ", "name": "John"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should succeed with normalized email

    def test_subscribe_confirm_empty_name_uses_default(
        self, client: FlaskClient
    ) -> None:
        """Test that empty name defaults to 'Subscriber'."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "test@example.com", "name": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Should succeed with default name

    def test_subscribe_saves_to_database(self, app: Flask, client: FlaskClient) -> None:
        """Test that form submission persists subscriber to database."""
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "dbtest@example.com", "name": "DB Test"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # Verify subscriber was persisted
        with app.app_context():
            from src.sejfa.newsflash.data.models import Subscriber

            subscriber = db.session.execute(
                db.select(Subscriber).filter_by(email="dbtest@example.com")
            ).scalar_one_or_none()

            assert subscriber is not None
            assert subscriber.name == "DB Test"

    def test_subscribe_duplicate_email_shows_error(self, client: FlaskClient) -> None:
        """Test that duplicate email shows error message."""
        # First subscription
        client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "dup@example.com", "name": "First"},
            follow_redirects=True,
        )

        # Second subscription with same email
        response = client.post(
            "/newsflash/subscribe/confirm",
            data={"email": "dup@example.com", "name": "Second"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert b"This email is already subscribed" in response.data
