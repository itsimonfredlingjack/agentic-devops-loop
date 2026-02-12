"""Tests for News Flash data layer - Subscriber model and repository."""

from __future__ import annotations

import pytest
from flask import Flask

from src.sejfa.newsflash.data.models import Subscriber, db
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


class TestSubscriberModel:
    """Test Subscriber SQLAlchemy model."""

    def test_subscriber_has_required_columns(self, app: Flask) -> None:
        """Subscriber model should have id, email, name, subscribed_at."""
        with app.app_context():
            subscriber = Subscriber(
                email="test@example.com",
                name="Test User",
            )
            db.session.add(subscriber)
            db.session.commit()

            assert subscriber.id is not None
            assert subscriber.email == "test@example.com"
            assert subscriber.name == "Test User"
            assert subscriber.subscribed_at is not None

    def test_subscriber_email_is_unique(self, app: Flask) -> None:
        """Duplicate email should raise IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            sub1 = Subscriber(email="dup@example.com", name="User 1")
            db.session.add(sub1)
            db.session.commit()

            sub2 = Subscriber(email="dup@example.com", name="User 2")
            db.session.add(sub2)
            with pytest.raises(IntegrityError):
                db.session.commit()


class TestSubscriberRepository:
    """Test SubscriberRepository methods."""

    def test_create_returns_subscriber(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """create() should return a Subscriber with an id."""
        with app.app_context():
            subscriber = repo.create(email="test@example.com", name="Test User")

            assert subscriber.id is not None
            assert subscriber.email == "test@example.com"
            assert subscriber.name == "Test User"
            assert subscriber.subscribed_at is not None

    def test_find_by_email_returns_subscriber(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """find_by_email() should return the subscriber if found."""
        with app.app_context():
            repo.create(email="find@example.com", name="Finder")

            found = repo.find_by_email("find@example.com")

            assert found is not None
            assert found.email == "find@example.com"
            assert found.name == "Finder"

    def test_find_by_email_returns_none_when_not_found(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """find_by_email() should return None if email not found."""
        with app.app_context():
            found = repo.find_by_email("nonexistent@example.com")

            assert found is None

    def test_exists_returns_true_for_existing_email(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """exists() should return True for existing email."""
        with app.app_context():
            repo.create(email="exists@example.com", name="Exists")

            assert repo.exists("exists@example.com") is True

    def test_exists_returns_false_for_nonexistent_email(
        self, app: Flask, repo: SubscriberRepository
    ) -> None:
        """exists() should return False for nonexistent email."""
        with app.app_context():
            assert repo.exists("nope@example.com") is False
