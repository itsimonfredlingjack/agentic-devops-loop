"""
NewsArticle data model.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsArticle:
    """Represents a news article."""

    title: str
    content: str
    author: str
    published_date: datetime
    id: int | None = None
    category: str | None = None
