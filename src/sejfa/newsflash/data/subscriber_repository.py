"""Repository for News Flash subscriber data access."""

from __future__ import annotations

import csv
import io

from src.sejfa.newsflash.data.models import Subscriber, db


class SubscriberRepository:
    """Repository for Subscriber persistence via SQLAlchemy.

    Provides CRUD operations, search, export, and statistics
    for subscriber data access.
    """

    def find_by_email(self, email: str) -> Subscriber | None:
        """Find a subscriber by email address.

        Args:
            email: Email address to search for.

        Returns:
            Subscriber if found, None otherwise.
        """
        return db.session.execute(
            db.select(Subscriber).filter_by(email=email)
        ).scalar_one_or_none()

    def exists(self, email: str) -> bool:
        """Check if a subscriber with the given email exists.

        Args:
            email: Email address to check.

        Returns:
            True if subscriber exists, False otherwise.
        """
        return self.find_by_email(email) is not None

    def create(self, email: str, name: str) -> Subscriber:
        """Create a new subscriber.

        Args:
            email: Subscriber email address.
            name: Subscriber name.

        Returns:
            The created Subscriber instance.
        """
        subscriber = Subscriber(email=email, name=name)
        db.session.add(subscriber)
        db.session.commit()
        return subscriber

    def list_all(self) -> list[Subscriber]:
        """List all subscribers.

        Returns:
            List of all subscribers.
        """
        return list(db.session.execute(db.select(Subscriber)).scalars().all())

    def get_by_id(self, subscriber_id: int) -> Subscriber | None:
        """Get a subscriber by ID.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            Subscriber if found, None otherwise.
        """
        return db.session.get(Subscriber, subscriber_id)

    def update(
        self,
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
            Updated subscriber or None if not found.
        """
        subscriber = db.session.get(Subscriber, subscriber_id)
        if not subscriber:
            return None

        if email is not None:
            subscriber.email = email
        if name is not None:
            subscriber.name = name
        if active is not None:
            subscriber.active = active

        db.session.commit()
        return subscriber

    def delete(self, subscriber_id: int) -> bool:
        """Delete a subscriber.

        Args:
            subscriber_id: Subscriber ID.

        Returns:
            True if deleted, False if not found.
        """
        subscriber = db.session.get(Subscriber, subscriber_id)
        if not subscriber:
            return False

        db.session.delete(subscriber)
        db.session.commit()
        return True

    def search(self, query: str) -> list[Subscriber]:
        """Search subscribers by email or name.

        Args:
            query: Search query.

        Returns:
            List of matching subscribers.
        """
        pattern = f"%{query}%"
        return list(
            db.session.execute(
                db.select(Subscriber).filter(
                    db.or_(
                        Subscriber.email.ilike(pattern),
                        Subscriber.name.ilike(pattern),
                    )
                )
            )
            .scalars()
            .all()
        )

    def export_csv(self) -> str:
        """Export subscribers as CSV.

        Returns:
            CSV data as a string.
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "email", "name", "subscribed_date", "active"],
        )
        writer.writeheader()
        for subscriber in self.list_all():
            writer.writerow(
                {
                    "id": subscriber.id,
                    "email": subscriber.email,
                    "name": subscriber.name,
                    "subscribed_date": subscriber.subscribed_at.strftime("%Y-%m-%d"),
                    "active": subscriber.active,
                }
            )
        return output.getvalue()

    def get_statistics(self) -> dict:
        """Get subscriber statistics.

        Returns:
            Dictionary with total, active, and inactive counts.
        """
        total = db.session.execute(db.select(db.func.count(Subscriber.id))).scalar_one()
        active = db.session.execute(
            db.select(db.func.count(Subscriber.id)).filter(Subscriber.active.is_(True))
        ).scalar_one()
        return {
            "total_subscribers": total,
            "active_subscribers": active,
            "inactive_subscribers": total - active,
        }
