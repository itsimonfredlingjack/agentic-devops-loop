"""Tests for SubscriptionService.subscribe() with repository integration."""

from __future__ import annotations

import pytest
from flask import Flask

from src.sejfa.newsflash.business.subscription_service import (
    SubscriptionService,
    ValidationError,
)
from src.sejfa.newsflash.data.models import db
from src.sejfa.newsflash.data.subscriber_repository import SubscriberRepository


@pytest.fixture
def app() -> Flask:
    """Create test application with in-memory SQLite database."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def repo(app: Flask) -> SubscriberRepository:
    """Create a SubscriberRepository instance."""
    return SubscriberRepository()


@pytest.fixture
def service(repo: SubscriberRepository) -> SubscriptionService:
    """Create a SubscriptionService with repository."""
    return SubscriptionService(repository=repo)


class TestSubscribeMethod:
    """Test SubscriptionService.subscribe() method."""

    def test_subscribe_creates_subscriber_in_db(
        self, app: Flask, service: SubscriptionService, repo: SubscriberRepository
    ) -> None:
        """subscribe() should persist subscriber to database."""
        with app.app_context():
            result = service.subscribe("test@example.com", "Test User")

            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"
            assert "subscribed_at" in result

            # Verify persisted
            found = repo.find_by_email("test@example.com")
            assert found is not None
            assert found.name == "Test User"

    def test_subscribe_normalizes_email(
        self, app: Flask, service: SubscriptionService, repo: SubscriberRepository
    ) -> None:
        """subscribe() should normalize email before saving."""
        with app.app_context():
            service.subscribe("  TEST@EXAMPLE.COM  ", "User")

            found = repo.find_by_email("test@example.com")
            assert found is not None

    def test_subscribe_normalizes_name(
        self, app: Flask, service: SubscriptionService
    ) -> None:
        """subscribe() should normalize name."""
        with app.app_context():
            result = service.subscribe("test@example.com", "  John  ")
            assert result["name"] == "John"

    def test_subscribe_empty_name_uses_default(
        self, app: Flask, service: SubscriptionService
    ) -> None:
        """subscribe() should use 'Subscriber' for empty name."""
        with app.app_context():
            result = service.subscribe("test@example.com", "")
            assert result["name"] == "Subscriber"

    def test_subscribe_invalid_email_raises_validation_error(
        self, app: Flask, service: SubscriptionService
    ) -> None:
        """subscribe() should raise ValidationError for invalid email."""
        with app.app_context():
            with pytest.raises(ValidationError, match="Invalid email format"):
                service.subscribe("invalid", "User")

    def test_subscribe_duplicate_email_raises_validation_error(
        self, app: Flask, service: SubscriptionService
    ) -> None:
        """subscribe() should raise ValidationError for duplicate email."""
        with app.app_context():
            service.subscribe("dup@example.com", "User 1")

            with pytest.raises(
                ValidationError, match="This email is already subscribed"
            ):
                service.subscribe("dup@example.com", "User 2")

    def test_subscribe_duplicate_email_case_insensitive(
        self, app: Flask, service: SubscriptionService
    ) -> None:
        """subscribe() should detect duplicates regardless of case."""
        with app.app_context():
            service.subscribe("test@example.com", "User 1")

            with pytest.raises(
                ValidationError, match="This email is already subscribed"
            ):
                service.subscribe("TEST@EXAMPLE.COM", "User 2")


class TestSubscriptionServiceDI:
    """Test SubscriptionService dependency injection."""

    def test_service_without_repository_still_validates(self) -> None:
        """Service without repository should still validate and process."""
        service = SubscriptionService()
        result = service.process_subscription("test@example.com", "User")

        assert result["email"] == "test@example.com"

    def test_service_with_repository_has_subscribe(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """Service with repository should have subscribe() method."""
        service = SubscriptionService(repository=repo)
        assert hasattr(service, "subscribe")
