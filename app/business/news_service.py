"""
Business logic for news article management.
"""

from datetime import datetime

from app.data.models.news_article import NewsArticle
from app.data.repositories.news_repository import NewsRepository


class ValidationError(Exception):
    """Raised when business rule validation fails."""

    pass


class NewsService:
    """Service layer for news article operations."""

    def __init__(self, repository: NewsRepository):
        """Initialize service with repository dependency."""
        self.repository = repository

    def create_article(
        self, title: str, content: str, author: str, category: str = None
    ) -> NewsArticle:
        """
        Create a new news article.

        Args:
            title: Article title
            content: Article content
            author: Article author
            category: Optional category

        Returns:
            Created NewsArticle with assigned ID

        Raises:
            ValidationError: If business rules are violated
        """
        # Validate title
        if not title or not title.strip():
            raise ValidationError("Titel får inte vara tom")

        # Validate content
        if len(content) < 10:
            raise ValidationError("Innehåll måste vara minst 10 tecken")

        # Validate author
        if not author or not author.strip():
            raise ValidationError("Författare får inte vara tom")

        # Check for duplicate title
        if self.repository.exists_by_title(title):
            raise ValidationError("En artikel med denna titel finns redan")

        # Create article
        article = NewsArticle(
            title=title,
            content=content,
            author=author,
            published_date=datetime.now(),
            category=category,
        )

        # Persist and return
        return self.repository.add(article)

    def get_all_articles(self) -> list[NewsArticle]:
        """Retrieve all articles."""
        return self.repository.get_all()

    def get_article_by_id(self, article_id: int) -> NewsArticle | None:
        """Retrieve article by ID."""
        return self.repository.get_by_id(article_id)
