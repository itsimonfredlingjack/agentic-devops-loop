"""Tests for News Flash subscription service."""

from __future__ import annotations

import pytest

from src.sejfa.newsflash.business.subscription_service import (
    SubscriptionService,
    ValidationError,
)


class TestSubscriptionServiceEmailValidation:
    """Test SubscriptionService email validation."""

    def test_validate_empty_email_returns_false_with_error(self) -> None:
        """Test that empty email returns (False, 'Email is required')."""
        service = SubscriptionService()
        valid, message = service.validate_email("")

        assert valid is False
        assert message == "Email is required"

    def test_validate_none_email_returns_false_with_error(self) -> None:
        """Test that None email returns (False, 'Email is required')."""
        service = SubscriptionService()
        valid, message = service.validate_email(None)

        assert valid is False
        assert message == "Email is required"

    def test_validate_invalid_email_returns_false_with_error(self) -> None:
        """Test that invalid email returns (False, 'Invalid email format')."""
        service = SubscriptionService()
        valid, message = service.validate_email("invalid")

        assert valid is False
        assert message == "Invalid email format"

    def test_validate_invalid_email_no_at_sign(self) -> None:
        """Test that email without @ is invalid."""
        service = SubscriptionService()
        valid, message = service.validate_email("notanemail.com")

        assert valid is False
        assert message == "Invalid email format"

    def test_validate_invalid_email_no_domain(self) -> None:
        """Test that email without domain is invalid."""
        service = SubscriptionService()
        valid, message = service.validate_email("user@")

        assert valid is False
        assert message == "Invalid email format"

    def test_validate_valid_email_returns_true(self) -> None:
        """Test that valid email returns (True, '')."""
        service = SubscriptionService()
        valid, message = service.validate_email("test@example.com")

        assert valid is True
        assert message == ""

    def test_validate_valid_email_with_subdomain(self) -> None:
        """Test that valid email with subdomain is accepted."""
        service = SubscriptionService()
        valid, message = service.validate_email("user@mail.example.com")

        assert valid is True
        assert message == ""


class TestSubscriptionServiceNormalization:
    """Test SubscriptionService normalization methods."""

    def test_normalize_email_lowercase(self) -> None:
        """Test that normalize_email converts to lowercase."""
        service = SubscriptionService()
        normalized = service.normalize_email("TEST@EXAMPLE.COM")

        assert normalized == "test@example.com"

    def test_normalize_email_strip_whitespace(self) -> None:
        """Test that normalize_email strips whitespace."""
        service = SubscriptionService()
        normalized = service.normalize_email("  test@example.com  ")

        assert normalized == "test@example.com"

    def test_normalize_email_both_lowercase_and_strip(self) -> None:
        """Test that normalize_email does both lowercase and strip."""
        service = SubscriptionService()
        normalized = service.normalize_email("  TEST@EXAMPLE.COM  ")

        assert normalized == "test@example.com"

    def test_normalize_name_strip_whitespace(self) -> None:
        """Test that normalize_name strips whitespace."""
        service = SubscriptionService()
        normalized = service.normalize_name("  John Doe  ")

        assert normalized == "John Doe"

    def test_normalize_name_empty_returns_default(self) -> None:
        """Test that normalize_name returns 'Subscriber' for empty string."""
        service = SubscriptionService()
        normalized = service.normalize_name("")

        assert normalized == "Subscriber"

    def test_normalize_name_none_returns_default(self) -> None:
        """Test that normalize_name returns 'Subscriber' for None."""
        service = SubscriptionService()
        normalized = service.normalize_name(None)

        assert normalized == "Subscriber"

    def test_normalize_name_whitespace_only_returns_default(self) -> None:
        """Test that normalize_name returns 'Subscriber' for whitespace-only."""
        service = SubscriptionService()
        normalized = service.normalize_name("   ")

        assert normalized == "Subscriber"


class TestSubscriptionServiceProcessing:
    """Test SubscriptionService process_subscription method."""

    def test_process_subscription_with_valid_data(self) -> None:
        """Test process_subscription with valid email and name."""
        service = SubscriptionService()
        result = service.process_subscription("TEST@EXAMPLE.COM", "John Doe")

        assert result["email"] == "test@example.com"
        assert result["name"] == "John Doe"
        assert "subscribed_at" in result

    def test_process_subscription_normalizes_email(self) -> None:
        """Test that process_subscription normalizes email."""
        service = SubscriptionService()
        result = service.process_subscription("  TEST@EXAMPLE.COM  ", "John")

        assert result["email"] == "test@example.com"

    def test_process_subscription_normalizes_name(self) -> None:
        """Test that process_subscription normalizes name."""
        service = SubscriptionService()
        result = service.process_subscription("test@example.com", "  John  ")

        assert result["name"] == "John"

    def test_process_subscription_empty_name_uses_default(self) -> None:
        """Test that process_subscription uses 'Subscriber' for empty name."""
        service = SubscriptionService()
        result = service.process_subscription("test@example.com", "")

        assert result["name"] == "Subscriber"

    def test_process_subscription_invalid_email_raises_error(self) -> None:
        """Test that process_subscription raises error for invalid email."""
        service = SubscriptionService()

        with pytest.raises(ValidationError) as exc_info:
            service.process_subscription("invalid", "John")

        assert "Invalid email format" in str(exc_info.value)

    def test_process_subscription_empty_email_raises_error(self) -> None:
        """Test that process_subscription raises error for empty email."""
        service = SubscriptionService()

        with pytest.raises(ValidationError) as exc_info:
            service.process_subscription("", "John")

        assert "Email is required" in str(exc_info.value)
