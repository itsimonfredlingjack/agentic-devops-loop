"""Integration tests for ExpenseTracker Flask routes."""

import pytest
from flask import Flask

from src.expense_tracker.business.service import ExpenseService
from src.expense_tracker.data.repository import InMemoryExpenseRepository
from src.expense_tracker.presentation.routes import create_expense_blueprint


@pytest.fixture
def app() -> Flask:
    """Create a test Flask application with expense tracker blueprint."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret-key-for-testing-only"

    # Set up DI - create repository and service
    repository = InMemoryExpenseRepository()
    service = ExpenseService(repository)

    # Register blueprint with DI
    blueprint = create_expense_blueprint(service)
    app.register_blueprint(blueprint)

    return app


@pytest.fixture
def client(app: Flask):
    """Create a test client."""
    return app.test_client()


class TestIndexRoute:
    """Test GET / route - list all expenses."""

    def test_index_returns_200(self, client) -> None:
        """Index page returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_renders_template(self, client) -> None:
        """Index page renders the correct template with Swedish title."""
        response = client.get("/")
        # Check for Swedish UI text
        assert "Utgifter" in response.data.decode("utf-8")

    def test_index_shows_empty_message(self, client) -> None:
        """Index page shows message when no expenses exist."""
        response = client.get("/")
        # Should indicate no expenses yet (Swedish)
        assert (
            "Inga utgifter" in response.data.decode("utf-8")
            or "inga" in response.data.decode("utf-8").lower()
        )


class TestAddRoute:
    """Test POST /add route - add new expense."""

    def test_add_valid_expense_redirects(self, client) -> None:
        """Adding valid expense redirects to index."""
        response = client.post(
            "/add",
            data={"title": "Lunch", "amount": "50.0", "category": "Mat"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/" in response.headers["Location"]

    def test_add_valid_expense_shows_in_list(self, client) -> None:
        """Adding valid expense shows it in the list."""
        client.post(
            "/add",
            data={"title": "Lunch", "amount": "50.0", "category": "Mat"},
        )
        response = client.get("/")
        data = response.data.decode("utf-8")
        assert "Lunch" in data
        assert "50" in data
        assert "Mat" in data

    def test_add_invalid_amount_shows_error(self, client) -> None:
        """Adding expense with invalid amount shows error."""
        response = client.post(
            "/add",
            data={"title": "Test", "amount": "-10", "category": "Mat"},
            follow_redirects=True,
        )
        data = response.data.decode("utf-8")
        # Should show error (Swedish)
        assert "större än 0" in data or "greater than 0" in data.lower()

    def test_add_empty_title_shows_error(self, client) -> None:
        """Adding expense with empty title shows error."""
        response = client.post(
            "/add",
            data={"title": "", "amount": "100", "category": "Mat"},
            follow_redirects=True,
        )
        data = response.data.decode("utf-8")
        # Should show error about empty title (Swedish)
        assert "tom" in data.lower() or "empty" in data.lower()

    def test_add_invalid_category_shows_error(self, client) -> None:
        """Adding expense with invalid category shows error."""
        response = client.post(
            "/add",
            data={"title": "Test", "amount": "100", "category": "InvalidCat"},
            follow_redirects=True,
        )
        data = response.data.decode("utf-8")
        # Should show error about invalid category (Swedish)
        assert "kategori" in data.lower() or "category" in data.lower()


class TestSummaryRoute:
    """Test GET /summary route - show total amount."""

    def test_summary_returns_200(self, client) -> None:
        """Summary page returns 200 OK."""
        response = client.get("/summary")
        assert response.status_code == 200

    def test_summary_shows_zero_when_empty(self, client) -> None:
        """Summary shows 0 when no expenses."""
        response = client.get("/summary")
        data = response.data.decode("utf-8")
        # Should show 0 or 0.00
        assert "0" in data

    def test_summary_shows_total_amount(self, client) -> None:
        """Summary shows correct total of all expenses."""
        # Add some expenses
        client.post("/add", data={"title": "A", "amount": "100", "category": "Mat"})
        client.post(
            "/add", data={"title": "B", "amount": "50", "category": "Transport"}
        )
        client.post("/add", data={"title": "C", "amount": "25", "category": "Boende"})

        response = client.get("/summary")
        data = response.data.decode("utf-8")
        # Total should be 175
        assert "175" in data

    def test_summary_has_swedish_title(self, client) -> None:
        """Summary page has Swedish title."""
        response = client.get("/summary")
        data = response.data.decode("utf-8")
        # Should have Swedish text for "summary" or "total"
        assert "Sammanfattning" in data or "Totalt" in data
