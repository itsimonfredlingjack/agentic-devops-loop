"""
Integration tests for news article routes.
Tests use Flask test client.
"""

import pytest

from app import create_app


@pytest.fixture
def app():
    """Create and configure test app."""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestArticleListRoute:
    """Test GET / route for listing articles."""

    def test_get_empty_article_list(self, client):
        """Should display page with title when no articles exist."""
        # Legacy news app is now mounted at /legacy
        response = client.get("/legacy/")

        assert response.status_code == 200
        assert "Nyhetsarkiv" in response.get_data(as_text=True)

    def test_get_article_list_with_articles(self, client):
        """Should display article titles when articles exist."""
        # Create test articles via legacy path
        client.post(
            "/legacy/article/new",
            data={
                "title": "Första artikeln",
                "content": "Detta är första artikelns innehåll.",
                "author": "Test Författare",
            },
        )
        client.post(
            "/legacy/article/new",
            data={
                "title": "Andra artikeln",
                "content": "Detta är andra artikelns innehåll.",
                "author": "Test Författare",
            },
        )

        response = client.get("/legacy/")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Första artikeln" in html
        assert "Andra artikeln" in html


class TestArticleCreationForm:
    """Test GET /article/new route for creation form."""

    def test_get_new_article_form(self, client):
        """Should display form with required fields."""
        response = client.get("/legacy/article/new")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Titel" in html or "title" in html.lower()
        assert "Innehåll" in html or "content" in html.lower()
        assert "Författare" in html or "author" in html.lower()


class TestArticleCreation:
    """Test POST /article/new route for creating articles."""

    def test_create_valid_article_redirects_to_list(self, client):
        """Should create article and redirect to list on success."""
        response = client.post(
            "/legacy/article/new",
            data={
                "title": "Test Artikel",
                "content": "Detta är testartikels innehåll.",
                "author": "Test Författare",
            },
            follow_redirects=False,
        )

        assert response.status_code == 302
        # Redirect location is usually relative or absolute depending on Flask config
        # With url_prefix, it should redirect to /legacy/
        assert "/legacy/" in response.location

    def test_create_article_with_empty_title_returns_error(self, client):
        """Should return 400 with error message for empty title."""
        response = client.post(
            "/legacy/article/new",
            data={
                "title": "",
                "content": "Valid content here.",
                "author": "Test Author",
            },
        )

        assert response.status_code == 400
        html = response.get_data(as_text=True)
        assert "Titel får inte vara tom" in html


class TestArticleDetail:
    """Test GET /article/<id> route for article details."""

    def test_get_existing_article_detail(self, client):
        """Should display full article content."""
        # Create article first
        client.post(
            "/legacy/article/new",
            data={
                "title": "Detail Test",
                "content": "This is the full content of the article.",
                "author": "Test Author",
            },
        )

        response = client.get("/legacy/article/1")

        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Detail Test" in html
        assert "This is the full content of the article." in html
        assert "Test Author" in html

    def test_get_nonexistent_article_returns_404(self, client):
        """Should return 404 for non-existent article."""
        response = client.get("/legacy/article/999")

        assert response.status_code == 404
