"""SQLAlchemy models for News Flash."""

from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Subscriber(db.Model):
    """Newsletter subscriber model.

    Attributes:
        id: Primary key.
        email: Unique, indexed email address.
        name: Subscriber name.
        subscribed_at: Timestamp when the subscriber was created.
        active: Whether the subscriber is active.
    """

    __tablename__ = "subscribers"

    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name: str = db.Column(db.String(255), nullable=False)
    subscribed_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.now
    )
    active: bool = db.Column(db.Boolean, nullable=False, default=True)
