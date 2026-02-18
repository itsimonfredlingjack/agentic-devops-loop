"""
Repository pattern for NewsArticle persistence.
"""
from typing import Protocol

from app.data.models.news_article import NewsArticle


class NewsRepository(Protocol):
    """Protocol defining repository interface for NewsArticle."""

    def add(self, article: NewsArticle) -> NewsArticle:
        """Add article to repository and return it with assigned ID."""
        ...

    def get_by_id(self, article_id: int) -> NewsArticle | None:
        """Retrieve article by ID, or None if not found."""
        ...

    def get_all(self) -> list[NewsArticle]:
        """Retrieve all articles."""
        ...

    def exists_by_title(self, title: str) -> bool:
        """Check if article with given title already exists."""
        ...


class InMemoryNewsRepository:
    """In-memory implementation of NewsRepository for testing."""

    def __init__(self):
        """Initialize empty repository."""
        self._articles: dict[int, NewsArticle] = {}
        self._next_id = 1

    def add(self, article: NewsArticle) -> NewsArticle:
        """Add article to repository and return it with assigned ID."""
        article.id = self._next_id
        self._articles[self._next_id] = article
        self._next_id += 1
        return article

    def get_by_id(self, article_id: int) -> NewsArticle | None:
        """Retrieve article by ID, or None if not found."""
        return self._articles.get(article_id)

    def get_all(self) -> list[NewsArticle]:
        """Retrieve all articles."""
        return list(self._articles.values())

    def exists_by_title(self, title: str) -> bool:
        """Check if article with given title already exists."""
        return any(article.title == title for article in self._articles.values())
