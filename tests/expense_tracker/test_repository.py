"""Unit tests for ExpenseRepository implementations."""

from src.expense_tracker.data.models import Expense
from src.expense_tracker.data.repository import InMemoryExpenseRepository


class TestInMemoryExpenseRepository:
    """Test InMemoryExpenseRepository implementation."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository = InMemoryExpenseRepository()

    def test_add_assigns_sequential_ids(self) -> None:
        """Adding expenses assigns sequential IDs."""
        expense1 = self.repository.add(
            Expense(id=0, title="Test1", amount=100.0, category="Mat")
        )
        expense2 = self.repository.add(
            Expense(id=0, title="Test2", amount=200.0, category="Transport")
        )

        assert expense1.id == 1
        assert expense2.id == 2

    def test_add_preserves_data(self) -> None:
        """Adding an expense preserves all data fields."""
        expense = self.repository.add(
            Expense(id=0, title="Lunch", amount=75.50, category="Mat")
        )

        assert expense.title == "Lunch"
        assert expense.amount == 75.50
        assert expense.category == "Mat"

    def test_get_all_empty_repository(self) -> None:
        """Getting all from empty repository returns empty list."""
        result = self.repository.get_all()
        assert result == []

    def test_get_all_returns_all_added(self) -> None:
        """Getting all returns all previously added expenses."""
        self.repository.add(Expense(id=0, title="Test1", amount=100.0, category="Mat"))
        self.repository.add(
            Expense(id=0, title="Test2", amount=200.0, category="Transport")
        )
        self.repository.add(
            Expense(id=0, title="Test3", amount=300.0, category="Boende")
        )

        result = self.repository.get_all()
        assert len(result) == 3

    def test_get_all_returns_copy(self) -> None:
        """Getting all returns a copy, not the internal list."""
        self.repository.add(Expense(id=0, title="Test", amount=100.0, category="Mat"))

        result1 = self.repository.get_all()
        result2 = self.repository.get_all()

        # Should be equal but not same object
        assert result1 == result2
        assert result1 is not result2

    def test_get_next_id_starts_at_one(self) -> None:
        """Next ID starts at 1 for empty repository."""
        assert self.repository.get_next_id() == 1

    def test_get_next_id_increments(self) -> None:
        """Next ID increments after adding."""
        assert self.repository.get_next_id() == 1
        self.repository.add(Expense(id=0, title="Test", amount=100.0, category="Mat"))
        assert self.repository.get_next_id() == 2
