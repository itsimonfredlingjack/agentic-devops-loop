"""Tests for the document upload Flask app."""
from datetime import datetime

import pytest

from app import app, format_filename


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_app_starts():
    """Test that app initializes without errors."""
    assert app is not None


def test_index_route_returns_200(client):
    """Test that GET / returns 200 status."""
    response = client.get('/')
    assert response.status_code == 200


def test_index_returns_html(client):
    """Test that index returns HTML content."""
    response = client.get('/')
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


def test_format_filename_includes_date():
    """Test that filename includes current date."""
    original_name = "document.pdf"
    formatted = format_filename(original_name)
    today = datetime.now().strftime("%Y%m%d")
    assert today in formatted
    assert "document" in formatted.lower()


def test_format_filename_preserves_extension():
    """Test that file extension is preserved."""
    test_cases = [
        ("test.pdf", ".pdf"),
        ("myfile.txt", ".txt"),
        ("document.docx", ".docx"),
    ]
    for original, expected_ext in test_cases:
        formatted = format_filename(original)
        assert formatted.endswith(expected_ext)


def test_upload_route_exists(client):
    """Test that upload route exists and accepts POST."""
    response = client.post('/upload')
    # Should not be 404
    assert response.status_code != 404
