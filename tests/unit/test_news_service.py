"""
Unit tests for NewsService business logic.
Tests use InMemoryRepository for isolation.
"""
import pytest
from datetime import datetime
from app.business.news_service import NewsService, ValidationError
from app.data.repositories.news_repository import InMemoryNewsRepository
from app.data.models.news_article import NewsArticle


class TestNewsServiceValidation:
    """Test business rule validation."""

    def setup_method(self):
        """Create fresh service and repository for each test."""
        self.repository = InMemoryNewsRepository()
        self.service = NewsService(self.repository)

    def test_create_valid_article(self):
        """Should create article with valid data."""
        article = self.service.create_article(
            title="Testartikel",
            content="Detta är en testartikels innehåll som är långt nog.",
            author="Test Författare"
        )

        assert article.id is not None
        assert article.title == "Testartikel"
        assert article.content == "Detta är en testartikels innehåll som är långt nog."
        assert article.author == "Test Författare"
        assert isinstance(article.published_date, datetime)

    def test_empty_title_raises_validation_error(self):
        """Should reject empty title."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_article(
                title="",
                content="Valid content here that is long enough.",
                author="Test Author"
            )

        assert str(exc_info.value) == "Titel får inte vara tom"

    def test_whitespace_only_title_raises_validation_error(self):
        """Should reject title with only whitespace."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_article(
                title="   ",
                content="Valid content here that is long enough.",
                author="Test Author"
            )

        assert str(exc_info.value) == "Titel får inte vara tom"

    def test_short_content_raises_validation_error(self):
        """Should reject content shorter than 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_article(
                title="Valid Title",
                content="Short",
                author="Test Author"
            )

        assert str(exc_info.value) == "Innehåll måste vara minst 10 tecken"

    def test_empty_author_raises_validation_error(self):
        """Should reject empty author."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_article(
                title="Valid Title",
                content="Valid content here that is long enough.",
                author=""
            )

        assert str(exc_info.value) == "Författare får inte vara tom"

    def test_duplicate_title_raises_validation_error(self):
        """Should reject article with duplicate title."""
        # First article succeeds
        self.service.create_article(
            title="Duplicate Title",
            content="First article content that is long enough.",
            author="First Author"
        )

        # Second article with same title fails
        with pytest.raises(ValidationError) as exc_info:
            self.service.create_article(
                title="Duplicate Title",
                content="Second article content that is long enough.",
                author="Second Author"
            )

        assert str(exc_info.value) == "En artikel med denna titel finns redan"


class TestNewsServiceRetrieval:
    """Test article retrieval operations."""

    def setup_method(self):
        """Create fresh service and repository for each test."""
        self.repository = InMemoryNewsRepository()
        self.service = NewsService(self.repository)

    def test_get_all_articles_returns_empty_list_initially(self):
        """Should return empty list when no articles exist."""
        articles = self.service.get_all_articles()
        assert articles == []

    def test_get_all_articles_returns_all_created_articles(self):
        """Should return all created articles."""
        article1 = self.service.create_article(
            title="First Article",
            content="First article content that is long enough.",
            author="Author One"
        )
        article2 = self.service.create_article(
            title="Second Article",
            content="Second article content that is long enough.",
            author="Author Two"
        )
        article3 = self.service.create_article(
            title="Third Article",
            content="Third article content that is long enough.",
            author="Author Three"
        )

        articles = self.service.get_all_articles()

        assert len(articles) == 3
        assert article1 in articles
        assert article2 in articles
        assert article3 in articles

    def test_get_article_by_id_returns_correct_article(self):
        """Should return article with matching ID."""
        created = self.service.create_article(
            title="Test Article",
            content="Test article content that is long enough.",
            author="Test Author"
        )

        retrieved = self.service.get_article_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == created.title
        assert retrieved.content == created.content
        assert retrieved.author == created.author

    def test_get_article_by_id_returns_none_for_nonexistent_id(self):
        """Should return None when article doesn't exist."""
        retrieved = self.service.get_article_by_id(999)
        assert retrieved is None
