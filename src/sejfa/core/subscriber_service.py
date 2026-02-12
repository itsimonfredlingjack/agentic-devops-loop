"""Subscriber management service."""

import csv
import io
from dataclasses import asdict, dataclass


@dataclass
class Subscriber:
    """Subscriber data model."""

    id: int
    email: str
    name: str
    subscribed_date: str
    active: bool = True


class SubscriberService:
    """Service for managing subscribers."""

    # In-memory storage for MVP
    _subscribers: dict[int, Subscriber] = {}
    _next_id: int = 1

    @classmethod
    def add_subscriber(cls, email: str, name: str, subscribed_date: str) -> Subscriber:
        """Add a new subscriber.

        Args:
            email: Subscriber email.
            name: Subscriber name.
            subscribed_date: Date subscriber signed up.

        Returns:
            Subscriber: Created subscriber.
        """
        subscriber = Subscriber(
            id=cls._next_id, email=email, name=name, subscribed_date=subscribed_date
        )
        cls._subscribers[cls._next_id] = subscriber
        cls._next_id += 1
        return subscriber

    @classmethod
    def list_subscribers(cls) -> list[Subscriber]:
        """List all subscribers.

        Returns:
            list[Subscriber]: List of subscribers.
        """
        return list(cls._subscribers.values())

    @classmethod
    def get_subscriber(cls, subscriber_id: int) -> Subscriber | None:
        """Get a subscriber by ID.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            Subscriber | None: Subscriber or None if not found.
        """
        return cls._subscribers.get(subscriber_id)

    @classmethod
    def update_subscriber(
        cls,
        subscriber_id: int,
        email: str | None = None,
        name: str | None = None,
        active: bool | None = None,
    ) -> Subscriber | None:
        """Update a subscriber.

        Args:
            subscriber_id: Subscriber ID.
            email: New email (optional).
            name: New name (optional).
            active: New active status (optional).

        Returns:
            Subscriber | None: Updated subscriber or None if not found.
        """
        subscriber = cls._subscribers.get(subscriber_id)
        if not subscriber:
            return None

        if email is not None:
            subscriber.email = email
        if name is not None:
            subscriber.name = name
        if active is not None:
            subscriber.active = active

        return subscriber

    @classmethod
    def delete_subscriber(cls, subscriber_id: int) -> bool:
        """Delete a subscriber.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            bool: True if deleted, False if not found.
        """
        if subscriber_id in cls._subscribers:
            del cls._subscribers[subscriber_id]
            return True
        return False

    @classmethod
    def search_subscribers(cls, query: str) -> list[Subscriber]:
        """Search subscribers by email or name.

        Args:
            query: Search query.

        Returns:
            list[Subscriber]: Matching subscribers.
        """
        query_lower = query.lower()
        return [
            s
            for s in cls._subscribers.values()
            if query_lower in s.email.lower() or query_lower in s.name.lower()
        ]

    @classmethod
    def export_csv(cls) -> str:
        """Export subscribers as CSV.

        Returns:
            str: CSV data.
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=["id", "email", "name", "subscribed_date", "active"]
        )
        writer.writeheader()
        for subscriber in cls._subscribers.values():
            writer.writerow(asdict(subscriber))
        return output.getvalue()

    @classmethod
    def reset(cls) -> None:
        """Reset the subscriber storage (for testing).

        Returns:
            None
        """
        cls._subscribers.clear()
        cls._next_id = 1

    @classmethod
    def get_statistics(cls) -> dict:
        """Get subscriber statistics.

        Returns:
            dict: Statistics data.
        """
        total = len(cls._subscribers)
        active = sum(1 for s in cls._subscribers.values() if s.active)
        return {
            "total_subscribers": total,
            "active_subscribers": active,
            "inactive_subscribers": total - active,
        }
