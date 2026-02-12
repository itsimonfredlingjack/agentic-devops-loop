"""Business logic for News Flash subscription handling.

This module contains the SubscriptionService which validates and normalizes
subscription data. It has NO Flask dependencies - pure Python only.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class ValidationError(Exception):
    """Raised when subscription validation fails."""

    pass


class SubscriptionService:
    """Service for validating and processing newsletter subscriptions.

    This service enforces:
    - Valid email format (regex validation)
    - Email normalization (lowercase, strip whitespace)
    - Name normalization (strip whitespace, default to "Subscriber")
    - Duplicate detection (when repository is provided)

    Args:
        repository: Optional SubscriberRepository for persistence.
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(self, repository: Any | None = None) -> None:
        """Initialize SubscriptionService.

        Args:
            repository: Optional repository for subscriber persistence.
        """
        self._repository = repository

    def validate_email(self, email: str | None) -> tuple[bool, str]:
        """Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
            - (True, "") if valid
            - (False, error_message) if invalid
        """
        if not email or (isinstance(email, str) and len(email.strip()) == 0):
            return False, "Email is required"

        # Strip whitespace before validation
        cleaned_email = email.strip()

        if not self.EMAIL_REGEX.match(cleaned_email):
            return False, "Invalid email format"

        return True, ""

    def normalize_email(self, email: str) -> str:
        """Normalize email address.

        Args:
            email: Email address to normalize

        Returns:
            Normalized email (lowercase, stripped)
        """
        return email.strip().lower()

    def normalize_name(self, name: str | None) -> str:
        """Normalize subscriber name.

        Args:
            name: Subscriber name to normalize

        Returns:
            Normalized name (stripped), or "Subscriber" if empty/None
        """
        if not name:
            return "Subscriber"

        normalized = name.strip()
        if not normalized:
            return "Subscriber"

        return normalized

    def process_subscription(self, email: str, name: str) -> dict[str, Any]:
        """Process a subscription with validation and normalization.

        Args:
            email: Email address
            name: Subscriber name

        Returns:
            Dictionary with:
            - email: Normalized email
            - name: Normalized name
            - subscribed_at: ISO timestamp

        Raises:
            ValidationError: If email validation fails
        """
        # Validate email first
        valid, error_message = self.validate_email(email)
        if not valid:
            raise ValidationError(error_message)

        # Normalize data
        normalized_email = self.normalize_email(email)
        normalized_name = self.normalize_name(name)

        # Return subscription data
        return {
            "email": normalized_email,
            "name": normalized_name,
            "subscribed_at": datetime.now().isoformat(),
        }

    def subscribe(self, email: str, name: str) -> dict[str, Any]:
        """Process subscription with validation, duplicate check, and persistence.

        Validates the email, normalizes data, checks for duplicates,
        and saves to the database via the repository.

        Args:
            email: Email address to subscribe.
            name: Subscriber name.

        Returns:
            Dictionary with email, name, and subscribed_at.

        Raises:
            ValidationError: If email is invalid or already subscribed.
        """
        # Validate and normalize via existing logic
        valid, error_message = self.validate_email(email)
        if not valid:
            raise ValidationError(error_message)

        normalized_email = self.normalize_email(email)
        normalized_name = self.normalize_name(name)

        # Check for duplicate
        if self._repository and self._repository.exists(normalized_email):
            raise ValidationError("This email is already subscribed")

        # Persist via repository
        if self._repository:
            subscriber = self._repository.create(
                email=normalized_email, name=normalized_name
            )
            return {
                "email": subscriber.email,
                "name": subscriber.name,
                "subscribed_at": subscriber.subscribed_at.isoformat(),
            }

        # Fallback if no repository (backwards compat)
        return {
            "email": normalized_email,
            "name": normalized_name,
            "subscribed_at": datetime.now().isoformat(),
        }
