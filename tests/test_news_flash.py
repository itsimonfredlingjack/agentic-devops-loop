"""Tests for News Flash newsletter app."""

from app import create_app

TEST_CONFIG = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
}


class TestNewsFlashIndex:
    """Tests for the News Flash index page."""

    def test_index_returns_200(self):
        """GET / should return HTTP 200."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_news_flash(self):
        """Index page should contain 'Built with care by Simon' text."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.get("/")
        assert b"Built with care by Simon" in response.data


class TestNewsFlashSubscribe:
    """Tests for the subscription form page."""

    def test_subscribe_returns_200(self):
        """GET /subscribe should return HTTP 200."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.get("/subscribe")
        assert response.status_code == 200

    def test_subscribe_contains_form(self):
        """Subscribe page should contain a form."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.get("/subscribe")
        assert b"<form" in response.data
        assert b"email" in response.data.lower()


class TestNewsFlashSubscribeConfirm:
    """Tests for the subscription confirmation."""

    def test_subscribe_confirm_returns_200(self):
        """POST /subscribe/confirm with valid data should redirect."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.post(
            "/subscribe/confirm",
            data={"email": "test@example.com", "name": "Test User"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_subscribe_confirm_shows_email(self):
        """Success message should be shown after subscription."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.post(
            "/subscribe/confirm",
            data={"email": "test@example.com", "name": "Test User"},
            follow_redirects=True,
        )
        assert b"prenumeration" in response.data.lower()

    def test_subscribe_confirm_shows_name(self):
        """Success message should include the submitted name."""
        app = create_app(TEST_CONFIG)
        client = app.test_client()
        response = client.post(
            "/subscribe/confirm",
            data={"email": "test@example.com", "name": "Test User"},
            follow_redirects=True,
        )
        assert b"Test User" in response.data
