"""Repository interfaces and implementations for ExpenseTracker."""

from abc import ABC, abstractmethod

from src.expense_tracker.data.models import Expense


class ExpenseRepository(ABC):
    """Abstract repository interface for expense storage."""

    @abstractmethod
    def add(self, expense: Expense) -> Expense:
        """Add an expense to storage.

        Args:
            expense: The expense to add.

        Returns:
            The added expense with assigned ID.
        """
        ...  # pragma: no cover

    @abstractmethod
    def get_all(self) -> list[Expense]:
        """Get all stored expenses.

        Returns:
            List of all expenses.
        """
        ...  # pragma: no cover

    @abstractmethod
    def get_next_id(self) -> int:
        """Get the next available ID.

        Returns:
            The next unique ID.
        """
        ...  # pragma: no cover


class InMemoryExpenseRepository(ExpenseRepository):
    """In-memory implementation of ExpenseRepository."""

    def __init__(self) -> None:
        """Initialize empty expense storage."""
        self._expenses: list[Expense] = []
        self._next_id: int = 1

    def add(self, expense: Expense) -> Expense:
        """Add an expense to in-memory storage.

        Args:
            expense: The expense to add.

        Returns:
            The added expense with assigned ID.
        """
        expense_with_id = Expense(
            id=self._next_id,
            title=expense.title,
            amount=expense.amount,
            category=expense.category,
        )
        self._expenses.append(expense_with_id)
        self._next_id += 1
        return expense_with_id

    def get_all(self) -> list[Expense]:
        """Get all stored expenses.

        Returns:
            List of all expenses.
        """
        return list(self._expenses)

    def get_next_id(self) -> int:
        """Get the next available ID.

        Returns:
            The next unique ID.
        """
        return self._next_id
