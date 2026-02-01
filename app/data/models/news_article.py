"""
NewsArticle data model.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NewsArticle:
    """Represents a news article."""

    title: str
    content: str
    author: str
    published_date: datetime
    id: Optional[int] = None
    category: Optional[str] = None
